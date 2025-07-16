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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def publish_chunk(msg: ChunkMessage):
    """
    Publishes a chunk message to the message queue.
    """
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
        logger.info("Message published successfully.")
    except Exception as e:
        logger.error(f"Failed to publish message: {e}")