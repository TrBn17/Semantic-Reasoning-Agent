import pytest

from semantic_reasoning_agent.infrastructure.ontology.chunking import chunk_for_extraction


def test_chunk_for_extraction_splits_with_overlap_and_cap() -> None:
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = chunk_for_extraction(text, window=10, overlap=2, max_chunks=3)
    assert chunks == ["abcdefghij", "ijklmnopqr", "qrstuvwxyz"]


def test_chunk_for_extraction_returns_single_chunk_for_short_text() -> None:
    assert chunk_for_extraction("hello world", window=100, overlap=10, max_chunks=8) == ["hello world"]


def test_chunk_for_extraction_window_zero_is_full_text_single_pass() -> None:
    long_text = "a" * 10_000
    assert chunk_for_extraction(long_text, window=0, overlap=500, max_chunks=8) == [long_text]
    assert chunk_for_extraction(" x ", window=0, overlap=0, max_chunks=1) == ["x"]


@pytest.mark.parametrize(
    ("window", "overlap", "max_chunks"),
    [
        (-1, 0, 1),
        (10, 10, 1),
        (10, -1, 1),
        (10, 0, 0),
    ],
)
def test_chunk_for_extraction_validates_arguments(window: int, overlap: int, max_chunks: int) -> None:
    with pytest.raises(ValueError):
        chunk_for_extraction("text", window=window, overlap=overlap, max_chunks=max_chunks)
