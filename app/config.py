"""
Configuration loader for the application.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings.
    """

    WORK_DIR: str = Field(
        default="/tmp/workdir",
        description="The working directory for cloning repositories.",
    )
    QUEUE_URL: str = Field(
        default="amqp://guest:guest@localhost:5672//",
        description="The URL of the RabbitMQ queue.",
    )
    MAX_CHUNK_SIZE: int = Field(
        default=1024,
        description="The maximum size of a chunk in bytes.",
    )
    PORT: int = Field(
        default=8000,
        description="The port to run the web server on.",
    )
    PROM_METRICS_PORT: int = Field(
        default=8001,
        description="The port to expose Prometheus metrics on.",
    )

    class Config:
        """
        Pydantic settings configuration.
        """

        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()