import os
from pathlib import Path
import pytest
from app.chunker import chunk_file


@pytest.fixture
def text_file(tmp_path: Path) -> Path:
    file_path = tmp_path / "test.txt"
    # Create a file with 2500 bytes
    file_path.write_bytes(b"a" * 2500)
    return file_path


def test_chunk_file_boundary_logic(text_file: Path):
    """
    Tests the boundary logic of the chunk_file function.
    """
    # Arrange
    max_bytes = 1024

    # Act
    chunks = list(chunk_file(text_file, max_bytes))
    total_size = sum(len(chunk_bytes) for _, chunk_bytes in chunks)

    # Assert
    assert len(chunks) == 3
    assert [offset for offset, _ in chunks] == [0, 1024, 2048]
    assert total_size == 2500


def test_chunk_small_text_file(tmp_path: Path):
    """
    Tests chunking a small text file with a small max_bytes value.
    """
    # Arrange
    file_path = tmp_path / "small.txt"
    content = b"abcdefghij"
    file_path.write_bytes(content)
    max_bytes = 5

    # Act
    chunks = list(chunk_file(file_path, max_bytes))

    # Assert
    assert chunks == [
        (0, b"abcde"),
        (5, b"fghij"),
    ]


def test_chunk_empty_file(tmp_path: Path):
    """
    Tests chunking an empty file.
    """
    # Arrange
    file_path = tmp_path / "empty.txt"
    file_path.touch()

    # Act
    chunks = list(chunk_file(file_path, 1024))

    # Assert
    assert chunks == []


def test_skip_binary_file(tmp_path: Path):
    """
    Tests that binary files are skipped.
    """
    # Arrange
    file_path = tmp_path / "binary.bin"
    file_path.write_bytes(b"\x00\x01\x02\x03\x04")

    # Act
    chunks = list(chunk_file(file_path, 1024))

    # Assert
    assert chunks == []