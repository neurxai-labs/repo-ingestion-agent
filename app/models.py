# Placeholder for models.py
from pydantic import BaseModel

class Repository(BaseModel):
    url: str

class CodeChunk(BaseModel):
    content: str
    repository: Repository


class ChunkMessage(BaseModel):
    repo_url: str
    chunk: CodeChunk