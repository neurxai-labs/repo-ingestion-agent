import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import db
from app.main import background_worker
from app.models import Base, Outbox, RepoRegister
from app.config import settings
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


import os
import tempfile
@patch("app.main.clone_repo")
def test_register_repo_e2e(mock_clone_repo, test_db):
    """
    End-to-end test for the /register-repo endpoint.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Arrange
        settings.WORK_DIR = tmpdir
        repo_path = os.path.join(settings.WORK_DIR, "test-repo")
        os.makedirs(repo_path, exist_ok=True)
        with open(os.path.join(repo_path, "test.py"), "w") as f:
            f.write("test")
        mock_clone_repo.return_value = repo_path
        repo_url = "https://github.com/test/repo.git"
        repo_id = "test-repo"
        repo = RepoRegister(repo_url=repo_url, repo_id=repo_id)
        session = db.SessionLocal()

        # Act
        background_worker(repo, session)

        # Assert
        outbox_items = session.query(Outbox).filter_by(repo_id=repo_id).all()
        assert len(outbox_items) > 0
        session.close()