import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(name: str = "app", log_dir: str = "logs"):
    """Cấu hình logging với console và file output"""
    
    # Tạo thư mục logs nếu chưa tồn tại
    Path(log_dir).mkdir(exist_ok=True)
    
    # Tạo logger chính
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Format log
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console Handler (INFO level)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler (DEBUG level) - Rotating file
    file_handler = RotatingFileHandler(
        f"{log_dir}/app.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Suppress verbose logs từ các libraries
    logging.getLogger("firebase_admin").setLevel(logging.WARNING)
    logging.getLogger("pyrebase").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    
    return logger

# Export logger
logger = setup_logger("chat-app")
