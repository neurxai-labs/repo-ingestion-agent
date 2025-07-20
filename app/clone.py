import os
import shutil
import logging
from pathlib import Path
import git

logger = logging.getLogger(__name__)

CLONE_ROOT = os.getenv("CLONE_ROOT", "/tmp/repos")

def clone_repo(url: str) -> Path:
    """
    Clones a repository into a directory based on the CLONE_ROOT environment
    variable.
    """
    repo_name = url.rstrip(".git").split("/")[-1]
    dest = os.path.join(CLONE_ROOT, repo_name)
    
    local_path = Path(dest)
    try:
        if local_path.exists():
            logger.info(
                "Directory already exists, deleting and re-cloning",
                extra={"repo_url": url, "path": str(local_path)},
            )
            shutil.rmtree(local_path)
        
        logger.info(
            "Cloning repository",
            extra={"repo_url": url, "path": str(local_path)},
        )
        git.Repo.clone_from(url, local_path)
        logger.info("Finished cloning", extra={"repo_url": url})
        return local_path
    except Exception as e:
        logger.error(
            "Failed to clone repository",
            extra={"repo_url": url, "error": str(e)},
        )
        raise