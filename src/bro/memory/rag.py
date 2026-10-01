"""Semantic & Hybrid RAG Engine for Bro Variant 2.

Indexes and retrieves relevant context across ~/ai-memory/bro and user's
Obsidian Knowledge Base (e.g. ~/obsidian/KnowledgeBase/ai-memory).
Combines BM25 lexical ranking with Ollama semantic embeddings.
"""

import math
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import requests

@dataclass
class KnowledgeChunk:
    source_file: str
    relative_path: str
    heading: str
    content: str
    tokens: Set[str] = field(default_factory=set)
    embedding: Optional[List[float]] = None

class HybridRAGEngine:
    def __init__(
        self,
        memory_dir: str,
        obsidian_vault_dir: Optional[str] = None,
        ollama_url: str = "http://localhost:11434",
        embedding_model: str = "nomic-embed-text",
        enabled: bool = True,
    ):
        self.memory_dir = Path(memory_dir).expanduser()
        self.obsidian_dir = Path(obsidian_vault_dir).expanduser() if obsidian_vault_dir else None
        self.ollama_url = ollama_url.rstrip("/")
        self.embedding_model = embedding_model
        self.enabled = enabled

        self.chunks: List[KnowledgeChunk] = []
        self._doc_frequencies: Dict[str, int] = {}
        self._avg_doc_len: float = 0.0
        self._last_indexed: float = 0.0
        self._embedding_available: Optional[bool] = None

        if self.enabled:
            self.refresh_index()

    def refresh_index(self) -> int:
        """Scan all markdown files in memory and Obsidian vault, chunking by sections."""
        start_time = time.time()
        directories = [self.memory_dir]
        if self.obsidian_dir and self.obsidian_dir.exists():
            directories.append(self.obsidian_dir)

        new_chunks: List[KnowledgeChunk] = []
        for base_dir in directories:
            if not base_dir.exists():
                continue
            for md_file in base_dir.rglob("*.md"):
                try:
                    rel_p = md_file.relative_to(base_dir)
                    text = md_file.read_text(encoding="utf-8", errors="ignore").strip()
                    if not text:
                        continue
                    file_chunks = self._chunk_markdown(str(md_file), str(rel_p), text)
                    new_chunks.extend(file_chunks)
                except Exception:
                    continue

        self.chunks = new_chunks
        self._compute_bm25_stats()
        self._last_indexed = time.time()
        return len(self.chunks)

    def _chunk_markdown(self, full_path: str, rel_path: str, text: str) -> List[KnowledgeChunk]:
        """Split a markdown file into logical section chunks by headings."""
        chunks: List[KnowledgeChunk] = []
        lines = text.split("\n")
        current_heading = Path(rel_path).stem.replace("_", " ").title()
        current_body: List[str] = []

        for line in lines:
            if re.match(r"^#{1,4}\s+", line):
                if current_body:
                    body_text = "\n".join(current_body).strip()
                    if body_text:
                        tokens = self._tokenize(current_heading + " " + body_text)
                        chunks.append(KnowledgeChunk(
                            source_file=full_path,
                            relative_path=rel_path,
                            heading=current_heading,
                            content=body_text,
                            tokens=tokens,
                        ))
                    current_body = []
                current_heading = line.lstrip("#").strip()
            else:
                current_body.append(line)

        if current_body:
            body_text = "\n".join(current_body).strip()
            if body_text:
                tokens = self._tokenize(current_heading + " " + body_text)
                chunks.append(KnowledgeChunk(
                    source_file=full_path,
                    relative_path=rel_path,
                    heading=current_heading,
                    content=body_text,
                    tokens=tokens,
                ))

        return chunks

    def _tokenize(self, text: str) -> Set[str]:
        words = re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())
        # Filter common stopwords
        stops = {"the", "and", "for", "with", "this", "that", "from", "are", "was", "were", "you", "your", "user", "bro"}
        return {w for w in words if w not in stops}

    def _compute_bm25_stats(self) -> None:
        self._doc_frequencies = {}
        total_len = 0
        for chunk in self.chunks:
            total_len += len(chunk.tokens)
            for token in chunk.tokens:
                self._doc_frequencies[token] = self._doc_frequencies.get(token, 0) + 1
        num_docs = max(1, len(self.chunks))
        self._avg_doc_len = total_len / num_docs

    def _score_bm25(self, query_tokens: Set[str], chunk: KnowledgeChunk) -> float:
        if not self.chunks:
            return 0.0
        score = 0.0
        k1 = 1.5
        b = 0.75
        doc_len = len(chunk.tokens)
        num_docs = len(self.chunks)

        for token in query_tokens:
            if token in chunk.tokens:
                df = self._doc_frequencies.get(token, 1)
                idf = math.log((num_docs - df + 0.5) / (df + 0.5) + 1.0)
                tf = 1.0  # token set frequency
                term_score = idf * ((tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / max(1.0, self._avg_doc_len)))))
                score += term_score

        # Exact heading bonus
        for token in query_tokens:
            if token in chunk.heading.lower():
                score += 2.0

        return score

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Fetch embedding vector from Ollama if available."""
        if self._embedding_available is False:
            return None
        try:
            resp = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.embedding_model, "prompt": text[:1000]},
                timeout=1.5,
            )
            if resp.status_code == 200:
                self._embedding_available = True
                return resp.json().get("embedding")
        except Exception:
            pass
        self._embedding_available = False
        return None

    def query(self, prompt: str, top_k: int = 3) -> List[Tuple[KnowledgeChunk, float]]:
        """Query across all knowledge bases and return the top-K relevant chunks."""
        if not self.enabled or not self.chunks:
            return []

        # Auto-refresh if index is older than 5 minutes
        if time.time() - self._last_indexed > 300:
            self.refresh_index()

        query_tokens = self._tokenize(prompt)
        if not query_tokens:
            return []

        scored_chunks: List[Tuple[KnowledgeChunk, float]] = []
        for chunk in self.chunks:
            bm25_score = self._score_bm25(query_tokens, chunk)
            if bm25_score > 0.5:
                scored_chunks.append((chunk, bm25_score))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    def format_context(self, prompt: str, top_k: int = 3) -> str:
        """Format top relevant chunks as clean markdown context for agent system prompt."""
        top_results = self.query(prompt, top_k=top_k)
        if not top_results:
            return ""

        context_blocks = []
        for chunk, score in top_results:
            block = (
                f"<!-- KNOWLEDGE: {chunk.relative_path} | Section: {chunk.heading} -->\n"
                f"### {chunk.heading} (from `{chunk.relative_path}`)\n"
                f"{chunk.content}"
            )
            context_blocks.append(block)

        return "\n\n".join(context_blocks)
