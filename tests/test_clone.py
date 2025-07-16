import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from app.clone import clone_repo
from app.config import settings

@pytest.fixture
def work_dir():
    work_dir = Path(settings.WORK_DIR)
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    yield work_dir
    shutil.rmtree(work_dir)

@patch('git.Repo.clone_from')
def test_clone_repo_success(mock_clone_from, work_dir):
    repo_url = "https://github.com/user/repo.git"
    repo_id = "test_repo"
    
    local_path = clone_repo(repo_url, repo_id)
    
    assert local_path == work_dir / repo_id
    mock_clone_from.assert_called_once_with(repo_url, local_path)

@patch('git.Repo.clone_from', side_effect=Exception("Failed to clone"))
def test_clone_repo_failure(mock_clone_from, work_dir):
    repo_url = "https://github.com/user/repo.git"
    repo_id = "test_repo"
    
    with pytest.raises(Exception):
        clone_repo(repo_url, repo_id)

def test_clone_repo_existing_directory(work_dir):
    repo_url = "https://github.com/Vishal-sys-code/Algorithms.git"
    repo_id = "test_repo"
    
    # Create a dummy directory
    (work_dir / repo_id).mkdir()

    with patch('git.Repo.clone_from') as mock_clone_from:
        local_path = clone_repo(repo_url, repo_id)
        assert local_path == work_dir / repo_id
        mock_clone_from.assert_called_once_with(repo_url, local_path)