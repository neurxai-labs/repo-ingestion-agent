from sqlalchemy import Column, Integer, String, Text, create_engine, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
import uuid

Base = declarative_base()

class Outbox(Base):
    __tablename__ = "outbox"
    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    offset = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint("repo_id", "file_path", "offset", name="uix_1"),)

class RepoRegister(BaseModel):
    """
    Represents a request to register a repository for processing.

    Example:
    {
        "repo_url": "https://github.com/example/repo"
    }
    """
    repo_url: HttpUrl
    repo_id: Optional[str] = None

    def generate_id(self) -> str:
        if self.repo_id:
            return self.repo_id
        self.repo_id = uuid.uuid4().hex
        return self.repo_id

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