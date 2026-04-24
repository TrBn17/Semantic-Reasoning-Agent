from __future__ import annotations


def chunk_for_extraction(
    text: str,
    *,
    window: int = 0,
    overlap: int = 500,
    max_chunks: int = 8,
) -> list[str]:
    """Split large markdown for extraction.

    When ``window`` is 0, return a single segment (full normalized text) so the
    extractor sees the full bounded markdown in one pass. When ``window`` is
    > 0, use an overlapping sliding window (legacy behavior).
    """
    normalized = text.strip()
    if not normalized:
        return []

    if max_chunks <= 0:
        raise ValueError("max_chunks must be > 0")
    if window == 0:
        return [normalized]
    if window < 0:
        raise ValueError("window must be >= 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= window:
        raise ValueError("overlap must be smaller than window")

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
