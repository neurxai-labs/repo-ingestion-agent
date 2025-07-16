import os
from pathlib import Path
import pytest
from app.chunker import chunk_file

@pytest.fixture
def text_file(tmp_path: Path) -> Path:
    file_path = tmp_path / "test.txt"
    file_path.write_text("line 1\r\nline 2\nline 3", newline='\n')
    return file_path

@pytest.fixture
def binary_file(tmp_path: Path) -> Path:
    file_path = tmp_path / "test.bin"
    file_path.write_bytes(b"some\x00binary\x00data")
    return file_path

def test_chunk_file_chunks(text_file: Path):
    chunks = list(chunk_file(text_file, 10))
    assert len(chunks) == 2
    assert chunks[0] == (0, b'line 1\nlin')
    assert chunks[1] == (10, b'e 2\nline 3')

def test_chunk_file_normalize_line_endings(text_file: Path):
    chunks = list(chunk_file(text_file, 100))
    assert len(chunks) == 1
    assert chunks[0] == (0, b'line 1\nline 2\nline 3')

def test_chunk_file_skip_binary(binary_file: Path):
    chunks = list(chunk_file(binary_file, 100))
    assert len(chunks) == 0
