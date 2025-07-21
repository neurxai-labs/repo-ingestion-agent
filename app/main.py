import logging
import os
from pathlib import Path
import sys
import time
print('sys.path:', sys.path)

import logging
import os
from pathlib import Path
import sys
import time
from fastapi import FastAPI, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from starlette.status import HTTP_202_ACCEPTED
from prometheus_client import start_http_server, Counter, Histogram
from app.chunker import chunk_file
from app.clone import clone_repo
from app.config import settings
from app.database import db
from app.models import RepoRegister, ChunkMessage, Outbox
from app.publisher import publisher_worker, CHUNKS_PUBLISHED_TOTAL
from app.logging_config import configure_logging
configure_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)
app = FastAPI()
REPOS_PROCESSED_TOTAL = Counter(
    "repos_processed_total", "Total number of repositories processed"
)
REPO_PROCESS_SECONDS = Histogram(
    "repo_process_seconds", "Time spent processing a repository"
)
@REPO_PROCESS_SECONDS.time()
def background_worker(repo: RepoRegister, db_session: Session):
    """
    Background worker to clone repo, chunk files, and save to outbox.
    """
    start_time = time.time()
    try:
        repo_path = clone_repo(repo.repo_url, repo.repo_id)
        logger.info(
            "Successfully cloned repo",
            extra={
                "repo_id": repo.repo_id,
                "repo_url": repo.repo_url,
                "path": str(repo_path),
            },
        )
        REPOS_PROCESSED_TOTAL.inc()
    except Exception as e:
        logger.error(
            "Error cloning repo",
            extra={"repo_id": repo.repo_id, "repo_url": repo.repo_url, "error": str(e)},
        )
        return
    outbox_items = []
    for file_path in Path(repo_path).rglob("*"):
        if file_path.is_file():
            try:
                for offset, chunk_bytes in chunk_file(
                    file_path, settings.MAX_CHUNK_SIZE
                ):
                    try:
                        chunk_text = chunk_bytes.decode("utf-8")
                        outbox_items.append(
                            Outbox(
                                repo_id=repo.repo_id,
                                file_path=str(
                                    file_path.relative_to(settings.WORK_DIR)
                                ),
                                offset=offset,
                                chunk_text=chunk_text,
                            )
                        )
                    except UnicodeDecodeError:
                        logger.warning(
                            "Could not decode file as UTF-8",
                            extra={
                                "repo_id": repo.repo_id,
                                "file_path": str(file_path),
                            },
                        )
            except Exception as e:
                logger.error(
                    "Error chunking file",
                    extra={
                        "repo_id": repo.repo_id,
                        "file_path": str(file_path),
                        "error": str(e),
                    },
                )
    try:
        db_session.add_all(outbox_items)
        db_session.commit()
        logger.info(
            "Saved chunks to outbox",
            extra={"repo_id": repo.repo_id, "num_chunks": len(outbox_items)},
        )
    except Exception as e:
        db_session.rollback()
        logger.error(
            "Error saving chunks to outbox",
            extra={"repo_id": repo.repo_id, "error": str(e)},
        )
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        "Finished processing repo",
        extra={"repo_id": repo.repo_id, "duration_ms": duration_ms},
    )


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/register-repo", status_code=HTTP_202_ACCEPTED)
async def register_repo(
    repo: RepoRegister,
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(db.get_db),
):
    """
    Endpoint to register a repository for processing.
    """
    logger.info(f"Received request to register repo: {repo.repo_url}")
    background_tasks.add_task(background_worker, repo, db_session)
    return JSONResponse(
        content={"message": "Repository registration accepted."},
        status_code=HTTP_202_ACCEPTED,
    )


def start():
    """
    Starts the uvicorn server and the publisher worker.
    """
    import uvicorn
    from threading import Thread
    db.init_db()
    publisher_thread = Thread(target=publisher_worker, daemon=True)
    publisher_thread.start()
    start_http_server(settings.PROM_METRICS_PORT)
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        log_config=None,
        reload=True,
    )


if __name__ == "__main__":
    start()