import sys
print(sys.path)
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)


def test_register_repo_schedules_task():
    """
    Tests that the /register-repo endpoint schedules a background task.
    """
    # Arrange
    repo_url = "https://example.com/foo.git"
    with patch("app.main.background_worker") as mock_background_worker:
        # Act
        response = client.post("/register-repo", json={"repo_url": repo_url})

        # Assert
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"
        mock_background_worker.assert_called_once()
