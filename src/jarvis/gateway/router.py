"""Enterprise LLM Gateway Router with cascading fallback, circuit breaking, and telemetry."""

import os
import time
from typing import Any, Dict, List, Optional
from jarvis.gateway.config import GatewayProviderConfig, GatewaySettings, get_default_gateway_settings
from jarvis.gateway.models import GatewayRequest, GatewayResponse, ProviderTelemetry
from jarvis.gateway.providers.base import BaseLLMProvider
from jarvis.gateway.providers.gemini import GeminiProvider
from jarvis.gateway.providers.groq import GroqProvider
from jarvis.gateway.providers.meta import MetaAIProvider
from jarvis.gateway.providers.ollama import OllamaGatewayProvider
from jarvis.gateway.providers.openai import OpenAIProvider
from jarvis.security.vault import SecretVault

class LLMGatewayRouter:
    def __init__(self, settings: Optional[GatewaySettings] = None, vault: Optional[SecretVault] = None):
        self.settings = settings or get_default_gateway_settings()
        self.vault = vault or SecretVault()
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.telemetry: Dict[str, ProviderTelemetry] = {}
        self._init_providers()

    def _init_providers(self) -> None:
        provider_classes = {
            "gemini": GeminiProvider,
            "openai": OpenAIProvider,
            "groq": GroqProvider,
            "meta": MetaAIProvider,
            "ollama": OllamaGatewayProvider,
        }
        for pid, pconf in self.settings.providers.items():
            cls = provider_classes.get(pid, BaseLLMProvider)
            self.providers[pid] = cls(pconf)
            self.telemetry[pid] = ProviderTelemetry(
                id=pid,
                display_name=pconf.display_name,
                enabled=pconf.enabled,
                healthy=True
            )

    def resolve_api_key(self, provider_id: str) -> Optional[str]:
        """Resolve API Key from config, Linux Keyring vault, or environment."""
        pconf = self.settings.providers.get(provider_id)
        if not pconf:
            return None
        if pconf.api_key and pconf.api_key.strip():
            return pconf.api_key.strip()
        if pconf.vault_key:
            vault_val = self.vault.get_secret(pconf.vault_key)
            if vault_val:
                return vault_val
        # Environment fallback
        env_map = {
            "gemini": "GEMINI_API_KEY",
            "openai": "OPENAI_API_KEY",
            "groq": "GROQ_API_KEY",
            "meta": "META_API_KEY",
        }
        env_var = env_map.get(provider_id)
        if env_var and os.getenv(env_var):
            return os.getenv(env_var)
        return None

    def get_ordered_providers(self, preferred_id: Optional[str] = None) -> List[str]:
        """Return provider IDs sorted by priority, placing preferred first if enabled."""
        enabled_pids = [
            pid for pid, p in self.settings.providers.items()
            if p.enabled
        ]
        now = time.time()
        # Filter out open circuits that haven't cooled down
        healthy_pids = []
        for pid in enabled_pids:
            telem = self.telemetry.get(pid)
            if telem and telem.circuit_open:
                if now >= telem.cooldown_until:
                    # Reset circuit for retry
                    telem.circuit_open = False
                    telem.consecutive_failures = 0
                    healthy_pids.append(pid)
            else:
                healthy_pids.append(pid)

        # Sort by priority
        healthy_pids.sort(key=lambda pid: self.settings.providers[pid].priority)

        # Move preferred to front if requested
        if preferred_id and preferred_id in healthy_pids:
            healthy_pids.remove(preferred_id)
            healthy_pids.insert(0, preferred_id)

        return healthy_pids

    def generate(self, request: GatewayRequest) -> GatewayResponse:
        """Execute completion with automated fallback cascading across providers."""
        ordered = self.get_ordered_providers(request.preferred_provider)
        if not ordered:
            return GatewayResponse(
                content="",
                model=request.model or "unknown",
                provider="none",
                success=False,
                error="No enabled LLM Gateway providers available."
            )

        last_error = ""
        for i, pid in enumerate(ordered):
            provider = self.providers.get(pid)
            if not provider:
                continue

            api_key = self.resolve_api_key(pid)
            telem = self.telemetry[pid]
            telem.total_requests += 1

            resp = provider.generate(request, resolved_api_key=api_key)

            if resp.success:
                telem.consecutive_failures = 0
                telem.healthy = True
                telem.last_ping_ms = resp.latency_ms
                telem.success_rate = round(
                    ((telem.total_requests - telem.total_errors) / max(1, telem.total_requests)) * 100, 1
                )
                if i > 0:
                    resp.fallback_used = True
                return resp
            else:
                last_error = resp.error or "Unknown error"
                telem.total_errors += 1
                telem.consecutive_failures += 1
                telem.success_rate = round(
                    ((telem.total_requests - telem.total_errors) / max(1, telem.total_requests)) * 100, 1
                )

                # Check circuit breaker
                if telem.consecutive_failures >= self.settings.circuit_breaker_threshold:
                    telem.circuit_open = True
                    telem.healthy = False
                    telem.cooldown_until = time.time() + self.settings.circuit_breaker_cooldown_sec

                if not self.settings.fallback_enabled:
                    break

        return GatewayResponse(
            content="",
            model=request.model or "unknown",
            provider="gateway",
            success=False,
            error=f"All configured providers failed. Last error: {last_error}"
        )

    def test_provider(self, provider_id: str) -> Dict[str, Any]:
        """Ping a specific provider and return diagnostic latency and status."""
        provider = self.providers.get(provider_id)
        if not provider:
            return {"success": False, "error": f"Provider '{provider_id}' not found."}
        api_key = self.resolve_api_key(provider_id)
        result = provider.ping(resolved_api_key=api_key)
        telem = self.telemetry.get(provider_id)
        if telem:
            telem.last_ping_ms = result.get("latency_ms", 0.0)
            telem.healthy = result.get("success", False)
        return result

    def get_statuses(self) -> List[Dict[str, Any]]:
        """Return status telemetry and config overview for all providers."""
        out = []
        for pid, pconf in self.settings.providers.items():
            telem = self.telemetry.get(pid)
            has_key = bool(self.resolve_api_key(pid)) or pconf.is_local
            out.append({
                "id": pid,
                "display_name": pconf.display_name,
                "enabled": pconf.enabled,
                "model": pconf.model,
                "available_models": pconf.available_models,
                "priority": pconf.priority,
                "has_api_key": has_key,
                "is_local": pconf.is_local,
                "healthy": telem.healthy if telem else True,
                "circuit_open": telem.circuit_open if telem else False,
                "last_ping_ms": telem.last_ping_ms if telem else 0.0,
                "total_requests": telem.total_requests if telem else 0,
                "total_errors": telem.total_errors if telem else 0,
                "success_rate": telem.success_rate if telem else 100.0,
            })
        return out

    def toggle_provider(self, provider_id: str, enabled: bool) -> bool:
        if provider_id in self.settings.providers:
            self.settings.providers[provider_id].enabled = enabled
            if provider_id in self.telemetry:
                self.telemetry[provider_id].enabled = enabled
            return True
        return False

    def update_provider_config(self, provider_id: str, updates: Dict[str, Any]) -> bool:
        if provider_id in self.settings.providers:
            p = self.settings.providers[provider_id]
            for k, v in updates.items():
                if hasattr(p, k):
                    setattr(p, k, v)
            return True
        return False
