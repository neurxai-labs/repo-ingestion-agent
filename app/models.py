from pydantic import BaseModel, HttpUrl, constr

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
    repo_id: constr(regex='^[a-zA-Z0-9_-]+$')

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