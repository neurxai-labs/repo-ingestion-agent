import json
import logging
import time
import pika
from pika.exceptions import AMQPConnectionError, ChannelError
from prometheus_client import Counter
from app.config import settings
from app.database import db
from app.models import Outbox, ChunkMessage
logger = logging.getLogger(__name__)
CHUNKS_PUBLISHED_TOTAL = Counter(
    "chunks_published_total", "Total number of chunks published"
)
def publish_chunk(msg: ChunkMessage, max_retries: int = 3, backoff_factor: float = 0.1):
    """
    Publishes a chunk message to the message queue with retry logic.
    """
    retries = 0
    while retries < max_retries:
        try:
            connection = pika.BlockingConnection(
                pika.URLParameters(settings.QUEUE_URL)
            )
            channel = connection.channel()
            channel.queue_declare(queue="repo-chunks", durable=True)
            message_body = msg.model_dump_json()
            channel.basic_publish(
                exchange="",
                routing_key="repo-chunks",
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                ),
            )
            connection.close()
            CHUNKS_PUBLISHED_TOTAL.inc()
            logger.info(
                "Message published successfully",
                extra={
                    "repo_id": msg.repo_id,
                    "file_path": msg.file_path,
                    "offset": msg.offset,
                },
            )
            return True
        except (AMQPConnectionError, ChannelError) as e:
            logger.warning(
                "Connection/Channel error, retrying...",
                extra={"repo_id": msg.repo_id, "error": str(e), "retry_count": retries},
            )
            time.sleep(backoff_factor * (2**retries))
            retries += 1
            if retries >= max_retries:
                logger.error(
                    "Failed to publish message after multiple retries",
                    extra={"repo_id": msg.repo_id, "error": str(e)},
                )
                raise e
        except Exception as e:
            logger.error(
                "Failed to publish message",
                extra={"repo_id": msg.repo_id, "error": str(e)},
            )
            raise e
def publisher_worker():
    """
    Worker to publish messages from the outbox.
    """
    while True:
        session = next(db.get_db())
        try:
            messages = session.query(Outbox).limit(100).all()
            if not messages:
                time.sleep(1)
                continue
            for msg in messages:
                chunk_message = ChunkMessage(
                    repo_id=msg.repo_id,
                    file_path=msg.file_path,
                    offset=msg.offset,
                    chunk_text=msg.chunk_text,
                )
                if publish_chunk(chunk_message):
                    session.delete(msg)
                    session.commit()
                else:
                    session.rollback()
        finally:
            session.close()