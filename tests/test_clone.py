import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import git

import pytest
from app.clone import clone_repo


def test_clone_repo_creates_directory(tmp_path, monkeypatch):
    """
    Tests that clone_repo creates a directory and calls git.Repo.clone_from with the correct arguments.
    """
    # Arrange
    monkeypatch.setattr("app.clone.CLONE_ROOT", str(tmp_path))
    mock_repo = MagicMock()
    mock_clone_from = MagicMock(return_value=mock_repo)
    monkeypatch.setattr("git.Repo.clone_from", mock_clone_from)

    repo_url = "https://example.com/foo.git"
    repo_name = "foo"

    # Act
    result_path = clone_repo(repo_url)

    # Assert
    assert result_path == tmp_path / repo_name
    mock_clone_from.assert_called_once_with(repo_url, tmp_path / repo_name)


def test_clone_repo_recreates_existing_directory(tmp_path, monkeypatch):
    """
    Tests that clone_repo deletes and recreates an existing directory.
    """
    # Arrange
    monkeypatch.setattr("app.clone.CLONE_ROOT", str(tmp_path))
    repo_name = "existing-repo"
    existing_dir = tmp_path / repo_name
    existing_dir.mkdir()
    (existing_dir / "old_file.txt").touch()

    mock_repo = MagicMock()
    mock_clone_from = MagicMock(return_value=mock_repo)
    monkeypatch.setattr("git.Repo.clone_from", mock_clone_from)

    repo_url = f"https://example.com/{repo_name}.git"

    # Act
    clone_repo(repo_url)

    # Assert
    assert not (existing_dir / "old_file.txt").exists()
    mock_clone_from.assert_called_once_with(repo_url, existing_dir)


def test_clone_repo_handles_clone_errors(tmp_path, monkeypatch):
    """
    Tests that clone_repo raises an exception when git.Repo.clone_from fails.
    """
    # Arrange
    monkeypatch.setattr("app.clone.CLONE_ROOT", str(tmp_path))
    monkeypatch.setattr("git.Repo.clone_from", MagicMock(side_effect=git.exc.GitCommandError("clone", "mock error")))

    repo_url = "https://example.com/fail.git"

    # Act & Assert
    with pytest.raises(Exception):
        clone_repo(repo_url)