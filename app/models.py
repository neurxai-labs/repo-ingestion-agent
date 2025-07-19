from typing import Pattern
from pydantic import BaseModel, HttpUrl, constr, Field

class RepoRegister(BaseModel):
    """
    Represents a request to register a repository for processing.

    Example:
    {
        "repo_url": "https://github.com/example/repo",
        "repo_id": "example-repo"
    }
    """
    repo_url: HttpUrl
    repo_id: constr = Field(..., pattern='^[a-zA-Z0-9_-]+$')

class Repository(BaseModel):
    """
    Represents a repository.
    """
    url: HttpUrl

class CodeChunk(BaseModel):
    """
    Represents a chunk of code from a repository.
    """
    content: str
    repository: Repository

class ChunkMessage(BaseModel):
    """
    Represents a chunk of a file from a repository.

    Example:
    {
        "repo_id": "example-repo",
        "file_path": "src/main.py",
        "offset": 1024,
        "chunk_text": "def hello_world():\\n    print(\\"Hello, World!\\")"
    }
    """
    repo_id: str
    file_path: str
    offset: int
    chunk_text: str