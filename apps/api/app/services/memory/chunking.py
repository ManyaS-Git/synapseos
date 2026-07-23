"""Chunking service — splits content into embeddable chunks.

Supports:
- Sentence chunking
- Paragraph chunking
- Recursive chunking (splits by paragraphs, then sentences if too large)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.memory import ChunkingStrategy


@dataclass
class Chunk:
    """A chunk of content ready for embedding."""

    content: str
    index: int
    token_count: int


class ChunkingService:
    """Splits text content into chunks for embedding."""

    def __init__(
        self,
        max_chunk_size: int = 512,
        overlap: int = 50,
    ):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

    def chunk(
        self,
        content: str,
        strategy: ChunkingStrategy | str = ChunkingStrategy.RECURSIVE,
    ) -> list[Chunk]:
        """Split content into chunks using the specified strategy."""
        if isinstance(strategy, str):
            strategy = ChunkingStrategy(strategy)

        match strategy:
            case ChunkingStrategy.SENTENCE:
                return self._sentence_chunk(content)
            case ChunkingStrategy.PARAGRAPH:
                return self._paragraph_chunk(content)
            case ChunkingStrategy.RECURSIVE:
                return self._recursive_chunk(content)
            case _:
                return self._recursive_chunk(content)

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate (~4 chars per token)."""
        return max(1, len(text) // 4)

    def _sentence_chunk(self, content: str) -> list[Chunk]:
        """Split by sentences, merging small ones."""
        sentences = re.split(r"(?<=[.!?])\s+", content.strip())
        chunks: list[Chunk] = []
        current = ""
        index = 0

        for sentence in sentences:
            candidate = f"{current} {sentence}".strip() if current else sentence
            if self._estimate_tokens(candidate) > self.max_chunk_size and current:
                chunks.append(Chunk(
                    content=current,
                    index=index,
                    token_count=self._estimate_tokens(current),
                ))
                index += 1
                current = sentence
            else:
                current = candidate

        if current:
            chunks.append(Chunk(
                content=current,
                index=index,
                token_count=self._estimate_tokens(current),
            ))

        return chunks or [Chunk(content=content, index=0, token_count=self._estimate_tokens(content))]

    def _paragraph_chunk(self, content: str) -> list[Chunk]:
        """Split by paragraphs."""
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        chunks: list[Chunk] = []

        for i, para in enumerate(paragraphs):
            if self._estimate_tokens(para) > self.max_chunk_size:
                # Split large paragraphs by sentences
                sub_chunks = self._sentence_chunk(para)
                for sc in sub_chunks:
                    chunks.append(Chunk(
                        content=sc.content,
                        index=len(chunks),
                        token_count=sc.token_count,
                    ))
            else:
                chunks.append(Chunk(
                    content=para,
                    index=i,
                    token_count=self._estimate_tokens(para),
                ))

        return chunks or [Chunk(content=content, index=0, token_count=self._estimate_tokens(content))]

    def _recursive_chunk(self, content: str) -> list[Chunk]:
        """Recursive chunking: try paragraphs first, then sentences, then hard split."""
        if self._estimate_tokens(content) <= self.max_chunk_size:
            return [Chunk(content=content, index=0, token_count=self._estimate_tokens(content))]

        # Try paragraph split first
        para_chunks = self._paragraph_chunk(content)
        if all(c.token_count <= self.max_chunk_size for c in para_chunks):
            return para_chunks

        # Fall back to sentence split
        sent_chunks = self._sentence_chunk(content)
        if all(c.token_count <= self.max_chunk_size for c in sent_chunks):
            return sent_chunks

        # Hard split as last resort
        return self._hard_split(content)

    def _hard_split(self, content: str) -> list[Chunk]:
        """Hard split by character count as a fallback."""
        chunks: list[Chunk] = []
        chars_per_chunk = self.max_chunk_size * 4  # rough chars per token

        for i in range(0, len(content), chars_per_chunk):
            chunk_text = content[i : i + chars_per_chunk]
            chunks.append(Chunk(
                content=chunk_text,
                index=len(chunks),
                token_count=self._estimate_tokens(chunk_text),
            ))

        return chunks
