"""Hardware Sentinel: Proactive monitoring of GPU, CPU, RAM, and Disk space."""

import shutil
import subprocess
import time
from typing import Any, Callable, Dict, Optional
import psutil
from bro.config import SentinelConfig

class HardwareSentinel:
    def __init__(self, config: SentinelConfig, alert_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.alert_callback = alert_callback
        self.enabled = config.enabled

    def get_hardware_metrics(self) -> Dict[str, Any]:
        """Fetch current hardware stats."""
        root_disk = psutil.disk_usage("/")
        metrics = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_percent": psutil.virtual_memory().percent,
            "ram_used_gb": round(psutil.virtual_memory().used / (1024**3), 1),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "disk_percent": root_disk.percent,
            "disk_root_used_gb": round(root_disk.used / (1024**3), 1),
            "disk_root_total_gb": round(root_disk.total / (1024**3), 1),
            "disk_root_free_gb": round(root_disk.free / (1024**3), 1),
            "disk_hdd": None,
            "gpu_temp": None,
            "vram_used_mb": None,
            "vram_total_mb": None,
            "gpu_name": "Unknown",
        }

        # Check secondary storage /mnt/HDD-500GB if mounted
        try:
            import os
            if os.path.exists("/mnt/HDD-500GB"):
                hdd = psutil.disk_usage("/mnt/HDD-500GB")
                metrics["disk_hdd"] = {
                    "percent": hdd.percent,
                    "used_gb": round(hdd.used / (1024**3), 1),
                    "total_gb": round(hdd.total / (1024**3), 1),
                    "free_gb": round(hdd.free / (1024**3), 1),
                }
        except Exception:
            pass

        # Query nvidia-smi
        try:
            res = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,temperature.gpu,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0 and res.stdout.strip():
                parts = [p.strip() for p in res.stdout.strip().split(",")]
                if len(parts) >= 4:
                    metrics["gpu_name"] = parts[0]
                    metrics["gpu_temp"] = int(parts[1])
                    metrics["vram_used_mb"] = int(parts[2])
                    metrics["vram_total_mb"] = int(parts[3])
        except Exception:
            pass

        return metrics

    def check_and_alert(self) -> Optional[str]:
        """Check thresholds and emit alerts if needed."""
        if not self.enabled:
            return None

        m = self.get_hardware_metrics()
        alert = None

        if m["gpu_temp"] and m["gpu_temp"] >= self.config.gpu_temp_threshold:
            alert = f"⚠️ High GPU Temperature Alert: {m['gpu_temp']}°C (Threshold: {self.config.gpu_temp_threshold}°C)"

        elif m["disk_percent"] >= self.config.disk_threshold_percent:
            alert = f"⚠️ Low Disk Space Alert: Root filesystem is {m['disk_percent']}% full!"

        if alert and self.alert_callback:
            self.alert_callback(alert)

        return alert
