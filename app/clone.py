import os
import shutil
import logging
from pathlib import Path
import git

logger = logging.getLogger(__name__)

def clone_repo(repo_url: str, repo_id: str) -> Path:
    from app.config import settings
    """
    Clones a repository into WORK_DIR/{repo_id}.

    If the directory already exists, it will be deleted and re-cloned.
    """
    local_path = Path(settings.WORK_DIR) / repo_id
    try:
        if local_path.exists():
            logger.info(
                "Directory already exists, deleting and re-cloning",
                extra={"repo_id": repo_id, "path": str(local_path)},
            )
            shutil.rmtree(local_path)
        
        logger.info(
            "Cloning repository",
            extra={"repo_id": repo_id, "repo_url": repo_url, "path": str(local_path)},
        )
        git.Repo.clone_from(repo_url, local_path)
        logger.info("Finished cloning", extra={"repo_id": repo_id})
        return local_path
    except Exception as e:
        logger.error(
            "Failed to clone repository",
            extra={"repo_id": repo_id, "repo_url": repo_url, "error": str(e)},
        )
        raise