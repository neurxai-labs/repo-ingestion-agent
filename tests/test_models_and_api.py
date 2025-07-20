import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from unittest.mock import patch

from app.main import app
from app.models import RepoRegister


def test_repo_register_valid_url():
    """
    Tests that RepoRegister accepts a valid URL.
    """
    repo = RepoRegister(repo_url="https://github.com/test/repo", repo_id="test-repo")
    assert str(repo.repo_url) == "https://github.com/test/repo"


def test_repo_register_invalid_url():
    """
    Tests that RepoRegister rejects an invalid URL.
    """
    with pytest.raises(ValidationError):
        RepoRegister(repo_url="not-a-url", repo_id="test-repo")


def test_register_repo_valid_payload():
    """
    Tests that the /register-repo endpoint returns a 202 on a valid payload.
    """
    client = TestClient(app)
    with patch("app.main.background_worker"):
        response = client.post("/register-repo", json={"repo_url": "https://github.com/test/repo", "repo_id": "test-repo"})
        assert response.status_code == 202
        assert response.json() == {"message": "Repository registration accepted."}


def test_register_repo_invalid_payload():
    """
    Tests that the /register-repo endpoint returns a 422 on an invalid payload.
    """
    client = TestClient(app)
    response = client.post("/register-repo", json={"repo_url": "not-a-url", "repo_id": "test-repo"})
    assert response.status_code == 422