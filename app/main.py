import logging
import os
from pathlib import Path
import sys
import time
import asyncio
from collections import deque
from fastapi import FastAPI, BackgroundTasks, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse, HTMLResponse, RedirectResponse, StreamingResponse
from starlette.status import HTTP_202_ACCEPTED, HTTP_302_FOUND
from prometheus_client import start_http_server, Counter, Histogram
from app.chunker import chunk_file
from app.clone import clone_repo
from app.config import settings
from app.database import db
from app.models import RepoRegister, ChunkMessage, Outbox
from app.publisher import publisher_worker, CHUNKS_PUBLISHED_TOTAL
from app.logging_config import configure_logging
from logging.handlers import QueueHandler
import queue

log_queue = queue.Queue()
configure_logging(settings.LOG_LEVEL, handler=QueueHandler(log_queue))
logger = logging.getLogger(__name__)
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
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


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/register-repo", status_code=HTTP_202_ACCEPTED)
async def register_repo(
    payload: RepoRegister,
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(db.get_db),
):
    """
    Endpoint to register a repository for processing.
    """
    repo_id = payload.generate_id()
    logger.info(f"Received request to register repo: {payload.repo_url}")
    background_tasks.add_task(background_worker, payload, db_session)
    return {"repo_id": repo_id, "status": "accepted"}


async def log_streamer():
    while True:
        try:
            log_record = log_queue.get_nowait()
            yield f"data: {log_record.getMessage()}\\n\\n"
        except queue.Empty:
            await asyncio.sleep(0.1)

@app.get("/logs")
async def logs():
    return StreamingResponse(log_streamer(), media_type="text/event-stream")


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