"""
Message publisher for the application.
"""
import json
import logging
import time

import pika
from pika.exceptions import AMQPConnectionError, ChannelError

from app.config import settings
from app.models import ChunkMessage

logger = logging.getLogger(__name__)


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
            logger.info(
                "Message published successfully",
                extra={"repo_id": msg.repo_id, "file_path": msg.file_path, "offset": msg.offset},
            )
            return
        except (AMQPConnectionError, ChannelError) as e:
            logger.warning(
                "Connection/Channel error, retrying...",
                extra={"repo_id": msg.repo_id, "error": str(e), "retry_count": retries},
            )
            retries += 1
            if retries >= max_retries:
                logger.error(
                    "Failed to publish message after multiple retries",
                    extra={"repo_id": msg.repo_id, "error": str(e)},
                )
                raise
            time.sleep(backoff_factor * (2 ** retries))
        except Exception as e:
            logger.error(
                "Failed to publish message",
                extra={"repo_id": msg.repo_id, "error": str(e)},
            )
            raise