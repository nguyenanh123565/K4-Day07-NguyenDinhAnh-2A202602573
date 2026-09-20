from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        
        # Cắt theo dấu câu nhưng giữ lại dấu câu nhờ look-behind regex
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = " ".join(sentences[i:i + self.max_sentences_per_chunk])
            chunks.append(chunk)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case 1: Text đã đủ nhỏ hơn chunk_size
        if len(current_text) <= self.chunk_size:
            return [current_text]
            
        # Base case 2: Hết separator để cắt, trả về nguyên trạng (fallback gracefully)
        if not remaining_separators:
            return [current_text]

        sep = remaining_separators[0]
        next_separators = remaining_separators[1:]

        splits = current_text.split(sep) if sep else list(current_text)
        
        good_splits = []
        for s in splits:
            if len(s) > self.chunk_size:
                good_splits.extend(self._split(s, next_separators))
            else:
                good_splits.append(s)

        # Gom các mảnh nhỏ lại cho tới sát giới hạn chunk_size
        final_chunks = []
        current_chunk = ""
        
        for s in good_splits:
            if not current_chunk:
                current_chunk = s
            elif len(current_chunk) + len(sep) + len(s) <= self.chunk_size:
                current_chunk += sep + s
            else:
                final_chunks.append(current_chunk)
                current_chunk = s
                
        if current_chunk:
            final_chunks.append(current_chunk)
            
        return final_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    mag_a = math.sqrt(sum(x * x for x in vec_a))
    mag_b = math.sqrt(sum(x * x for x in vec_b))
    
    # Chặn lỗi ZeroDivisionError nếu vector có độ lớn bằng 0
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
        
    return _dot(vec_a, vec_b) / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed = FixedSizeChunker(chunk_size=chunk_size, overlap=20)
        by_sent = SentenceChunker(max_sentences_per_chunk=3)
        recursive = RecursiveChunker(chunk_size=chunk_size)

        def get_stats(chunks):
            if not chunks:
                return {"count": 0, "avg_length": 0.0, "chunks": []}
            avg = sum(len(c) for c in chunks) / len(chunks)
            return {"count": len(chunks), "avg_length": avg, "chunks": chunks}

        return {
            "fixed_size": get_stats(fixed.chunk(text)),
            "by_sentences": get_stats(by_sent.chunk(text)),
            "recursive": get_stats(recursive.chunk(text))
        }