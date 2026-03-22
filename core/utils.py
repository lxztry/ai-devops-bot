"""Utility functions and decorators"""
import logging
import time
import functools
from pathlib import Path
from typing import Callable, Optional


def setup_logging(log_dir: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """Setup logging configuration"""
    logger = logging.getLogger("ai_coding_demo")
    logger.setLevel(level)
    
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry decorator with exponential backoff"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception
            raise last_exception
        return wrapper
    return decorator


def safe_execute(default=None):
    """Execute a function and return default value on exception"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                return default
        return wrapper
    return decorator
