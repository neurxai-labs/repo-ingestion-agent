import logging
import os
from pathlib import Path
import sys
import time
print('sys.path:', sys.path)

from fastapi import FastAPI, BackgroundTasks
from starlette.responses import JSONResponse
from starlette.status import HTTP_202_ACCEPTED
from prometheus_client import start_http_server, Counter, Histogram

from app.chunker import chunk_file
from app.clone import clone_repo
from app.config import settings
from app.models import RepoRegister, ChunkMessage
from app.publisher import publish_chunk
from app.logging_config import configure_logging

configure_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI()

# Prometheus metrics
REPOS_PROCESSED_TOTAL = Counter("repos_processed_total", "Total number of repositories processed")
CHUNKS_PUBLISHED_TOTAL = Counter("chunks_published_total", "Total number of chunks published")
REPO_PROCESS_SECONDS = Histogram("repo_process_seconds", "Time spent processing a repository")


@REPO_PROCESS_SECONDS.time()
def background_worker(repo: RepoRegister):
    """
    Background worker to clone repo, chunk files, and publish messages.
    """
    start_time = time.time()
    try:
        repo_path = clone_repo(repo.repo_url, repo.repo_id)
        logger.info(
            "Successfully cloned repo",
            extra={"repo_id": repo.repo_id, "repo_url": repo.repo_url, "path": str(repo_path)},
        )
        REPOS_PROCESSED_TOTAL.inc()
    except Exception as e:
        logger.error(
            "Error cloning repo",
            extra={"repo_id": repo.repo_id, "repo_url": repo.repo_url, "error": str(e)},
        )
        return

    for file_path in Path(repo_path).rglob("*"):
        if file_path.is_file():
            try:
                for offset, chunk_bytes in chunk_file(file_path, settings.MAX_CHUNK_SIZE):
                    try:
                        chunk_text = chunk_bytes.decode("utf-8")
                        chunk_message = ChunkMessage(
                            repo_id=repo.repo_id,
                            file_path=str(file_path.relative_to(settings.WORK_DIR)),
                            offset=offset,
                            chunk_text=chunk_text,
                        )
                        publish_chunk(chunk_message)
                        CHUNKS_PUBLISHED_TOTAL.inc()
                        logger.info(
                            "Published chunk",
                            extra={
                                "repo_id": repo.repo_id,
                                "file_path": str(file_path),
                                "offset": offset,
                            },
                        )
                    except UnicodeDecodeError:
                        logger.warning(
                            "Could not decode file as UTF-8",
                            extra={"repo_id": repo.repo_id, "file_path": str(file_path)},
                        )
                    except Exception as e:
                        logger.error(
                            "Error publishing chunk",
                            extra={
                                "repo_id": repo.repo_id,
                                "file_path": str(file_path),
                                "error": str(e),
                            },
                        )
            except Exception as e:
                logger.error(
                    "Error chunking file",
                    extra={"repo_id": repo.repo_id, "file_path": str(file_path), "error": str(e)},
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
async def register_repo(repo: RepoRegister, background_tasks: BackgroundTasks):
    """
    Endpoint to register a repository for processing.
    """
    logger.info(f"Received request to register repo: {repo.repo_url}")
    background_tasks.add_task(background_worker, repo)
    return JSONResponse(
        content={"message": "Repository registration accepted."},
        status_code=HTTP_202_ACCEPTED
    )


def start():
    """
    Starts the uvicorn server.
    """
    import uvicorn
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