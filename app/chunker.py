from pathlib import Path
from typing import Iterator, Tuple

def chunk_file(file_path: Path, max_bytes: int) -> Iterator[Tuple[int, bytes]]:
    """
    Reads a file in byte-length slices of up to max_bytes, yielding (offset, chunk_bytes).
    Skips binary vs. text appropriately and normalizes line endings.
    """
    with open(file_path, 'rb') as f:
        content = f.read()
    if b'\x00' in content:
        return
    content = content.replace(b'\r\n', b'\n')
    offset = 0
    while offset < len(content):
        chunk = content[offset:offset+max_bytes]
        yield offset, chunk
        offset += len(chunk)
