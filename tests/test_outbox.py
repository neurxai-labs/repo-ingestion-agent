import time
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import db
from app.main import app
from app.models import Base, Outbox
from app.config import settings
from fastapi.testclient import TestClient
@pytest.fixture(scope="module")
def test_db():
    """
    Pytest fixture to use a test database for the tests.
    """
    settings.DATABASE_URL = "sqlite:///:memory:"
    db.engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    db.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db.engine)
    Base.metadata.create_all(bind=db.engine)
    yield
    Base.metadata.drop_all(bind=db.engine)
from unittest.mock import patch


@patch("app.main.clone_repo")
def test_register_repo_e2e(mock_clone_repo, test_db):
    """
    End-to-end test for the /register-repo endpoint.
    """
    # Arrange
    mock_clone_repo.return_value = "/tmp/workdir/test-repo"
    client = TestClient(app)
    repo_url = "https://github.com/test/repo.git"
    repo_id = "test-repo"

    # Act
    response = client.post("/register-repo", json={"repo_url": repo_url, "repo_id": repo_id})

    # Assert
    assert response.status_code == 202
    time.sleep(1)  # Allow time for background task to run
    session = db.SessionLocal()
    outbox_items = session.query(Outbox).filter_by(repo_id=repo_id).all()
    assert len(outbox_items) > 0
    session.close()