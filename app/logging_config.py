import logging
import sys
from pythonjsonlogger import jsonlogger

def configure_logging(log_level="INFO", handler=None):
    """
    Configures logging to output JSON.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    if handler:
        logHandler = handler
    else:
        logHandler = logging.StreamHandler(sys.stdout)

    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    logHandler.setFormatter(formatter)
    
    # Avoid adding duplicate handlers
    if not logger.handlers:
        logger.addHandler(logHandler)

    # Configure uvicorn loggers to use the same handler
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.addHandler(logHandler)
    
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.addHandler(logHandler)
