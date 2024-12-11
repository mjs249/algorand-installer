# utils/logging_config.py
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logging(install_dir: Path) -> logging.Logger:
    """
    Configure logging for the installation process.
    
    Args:
        install_dir: Installation directory path
        
    Returns:
        Logger instance
    """
    # Create logs directory
    log_dir = install_dir / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'install_{timestamp}.log'
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup file handler
    file_handler = logging.handlers.RotatingFileHandler(
        str(log_file),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Setup logger
    logger = logging.getLogger('algorand_installer')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name or 'algorand_installer')
