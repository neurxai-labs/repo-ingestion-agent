import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from app.clone import clone_repo
from app.config import settings


def test_clone_repo_creates_directory(tmp_path, monkeypatch):
    """
    Tests that clone_repo creates a directory and calls git.Repo.clone_from with the correct arguments.
    """
    # Arrange
    monkeypatch.setattr(settings, "WORK_DIR", str(tmp_path))
    mock_repo = MagicMock()
    mock_clone_from = MagicMock(return_value=mock_repo)
    monkeypatch.setattr("git.Repo.clone_from", mock_clone_from)

    repo_url = "https://example.com/foo.git"
    repo_id = "foo-id"

    # Act
    result_path = clone_repo(repo_url, repo_id)

    # Assert
    assert result_path == tmp_path / repo_id
    mock_clone_from.assert_called_once_with(repo_url, tmp_path / repo_id)