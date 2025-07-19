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
