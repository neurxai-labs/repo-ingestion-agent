import json
from unittest.mock import MagicMock, patch

import pika
import pytest
from app.models import ChunkMessage
from app.publisher import publish_chunk


@pytest.fixture
def chunk_message() -> ChunkMessage:
    """
    Returns a ChunkMessage instance for testing.
    """
    return ChunkMessage(
        repo_id="test-repo",
        file_path="test_file.py",
        offset=0,
        chunk_text="test content",
    )


@patch("app.publisher.pika")
def test_publish_chunk_with_fake_kafka_stub(mock_pika, chunk_message: ChunkMessage):
    """
    Tests that publish_chunk sends the correct message to the correct topic.
    """
    # Arrange
    mock_channel = MagicMock()
    mock_connection = MagicMock()
    mock_connection.channel.return_value = mock_channel
    mock_pika.BlockingConnection.return_value = mock_connection

    # Act
    publish_chunk(chunk_message)

    # Assert
    mock_channel.basic_publish.assert_called_once()
    args, kwargs = mock_channel.basic_publish.call_args
    assert kwargs["exchange"] == ""
    assert kwargs["routing_key"] == "repo-chunks"
    sent_payload = json.loads(kwargs["body"])
    assert sent_payload == chunk_message.model_dump()


@patch("app.publisher.pika")
@patch("app.publisher.time.sleep", return_value=None)
def test_publish_chunk_with_retry(mock_sleep, mock_pika, chunk_message: ChunkMessage):
    """
    Tests that publish_chunk retries on connection failure and eventually raises an exception.
    """
    # Arrange
    mock_pika.BlockingConnection.side_effect = pika.exceptions.AMQPConnectionError

    # Act & Assert
    with pytest.raises(pika.exceptions.AMQPConnectionError):
        publish_chunk(chunk_message, max_retries=3)

    assert mock_pika.BlockingConnection.call_count == 3
    assert mock_sleep.call_count == 3