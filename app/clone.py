import os
import shutil
import logging
from pathlib import Path
import git
from app.config import settings

logging.basicConfig(level=logging.INFO)

def clone_repo(repo_url: str, repo_id: str) -> Path:
    """
    Clones a repository into WORK_DIR/{repo_id}.

    If the directory already exists, it will be deleted and re-cloned.
    """
    local_path = Path(settings.WORK_DIR) / repo_id
    try:
        if local_path.exists():
            logging.info(f"Directory {local_path} already exists. Deleting and re-cloning.")
            shutil.rmtree(local_path)
        
        logging.info(f"Cloning {repo_url} to {local_path}...")
        git.Repo.clone_from(repo_url, local_path)
        logging.info("Cloning complete.")
        return local_path
    except Exception as e:
        logging.error(f"Failed to clone repository: {e}")
        raise