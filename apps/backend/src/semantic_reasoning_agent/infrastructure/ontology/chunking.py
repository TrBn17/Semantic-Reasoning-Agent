from __future__ import annotations


def chunk_for_extraction(
    text: str,
    *,
    window: int = 6000,
    overlap: int = 500,
    max_chunks: int = 8,
) -> list[str]:
    """Split large markdown into overlapping windows for extraction."""
    normalized = text.strip()
    if not normalized:
        return []

    if window <= 0:
        raise ValueError("window must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= window:
        raise ValueError("overlap must be smaller than window")
    if max_chunks <= 0:
        raise ValueError("max_chunks must be > 0")

    chunks: list[str] = []
    step = window - overlap
    start = 0
    while start < len(normalized) and len(chunks) < max_chunks:
        end = min(len(normalized), start + window)
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start += step
    return chunks
