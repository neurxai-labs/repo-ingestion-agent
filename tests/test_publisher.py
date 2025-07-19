"""
Tests for the message publisher.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.models import ChunkMessage, CodeChunk, Repository
from app.publisher import publish_chunk


def test_publish_chunk_success(mocker):
    """
    Tests that publish_chunk successfully sends a message.
    """
    mock_pika = mocker.patch("app.publisher.pika")
    mock_connection = MagicMock()
    mock_channel = MagicMock()
    mock_pika.BlockingConnection.return_value = mock_connection
    mock_connection.channel.return_value = mock_channel

    repo = Repository(url="http://test.com/repo.git")
    chunk = CodeChunk(content="test content", repository=repo)
    msg = ChunkMessage(
        repo_id="test-repo",
        file_path="test_file.py",
        offset=0,
        chunk_text="test content",
    )

    publish_chunk(msg)

    mock_pika.BlockingConnection.assert_called_once()
    mock_connection.channel.assert_called_once()
    mock_channel.queue_declare.assert_called_once_with(
        queue="repo-chunks", durable=True
    )
    mock_channel.basic_publish.assert_called_once()
    mock_connection.close.assert_called_once()


def test_publish_chunk_failure(mocker):
    """
    Tests that publish_chunk handles connection errors.
    """
    mock_pika = mocker.patch("app.publisher.pika")
    mock_logger = mocker.patch("app.publisher.logger")
    mock_pika.BlockingConnection.side_effect = Exception("Connection error")

    repo = Repository(url="http://test.com/repo.git")
    chunk = CodeChunk(content="test content", repository=repo)
    msg = ChunkMessage(
        repo_id="test-repo",
        file_path="test_file.py",
        offset=0,
        chunk_text="test content",
    )

    publish_chunk(msg)

    mock_logger.error.assert_called_with(
        "Failed to publish message: Connection error"
    )