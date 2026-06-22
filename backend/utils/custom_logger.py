import logging
import os

# Read log level from environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def setup_logger(name: str) -> logging.Logger:
    """Configures a standardized structured logger for all API endpoints and services."""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger
