"""Utility functions and decorators"""
import logging
import time
import functools
import json
from pathlib import Path
from typing import Callable, Optional, Any, TypeVar
from datetime import datetime
from dataclasses import asdict, is_dataclass


T = TypeVar('T')


def setup_logging(
    log_dir: Optional[Path] = None, 
    level: int = logging.INFO,
    structured: bool = False
) -> logging.Logger:
    """Setup logging configuration"""
    logger = logging.getLogger("ai_coding_demo")
    logger.setLevel(level)
    
    if logger.handlers:
        return logger
    
    if structured:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
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


def retry(
    max_attempts: int = 3, 
    delay: float = 1.0, 
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Retry decorator with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception: BaseException = Exception("Unknown error")
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception
            raise last_exception
        return wrapper
    return decorator


def safe_execute(default: T = None, log_errors: bool = True, logger: Optional[logging.Logger] = None):
    """Execute a function and return default value on exception"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    log = logger or logging.getLogger(func.__module__)
                    log.warning(f"Error in {func.__name__}: {e}")
                return default
        return wrapper
    return decorator


class StructuredLogger:
    """Structured logging helper for JSON output"""
    
    def __init__(self, name: str, log_file: Optional[Path] = None):
        self.logger = logging.getLogger(name)
        self.log_file = log_file
    
    def _serialize(self, data: Any) -> Any:
        if is_dataclass(data) and not isinstance(data, type):
            data = asdict(data)
        if isinstance(data, dict):
            return {k: self._serialize(v) for k, v in data.items()}
        if isinstance(data, (list, tuple)):
            return [self._serialize(i) for i in data]
        return data
    
    def log(self, level: int, event: str, **kwargs):
        message = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            **kwargs
        }
        serialized = self._serialize(message)
        
        self.logger.log(level, json.dumps(serialized))
        
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(serialized) + "\n")
    
    def info(self, event: str, **kwargs):
        self.log(logging.INFO, event, **kwargs)
    
    def warning(self, event: str, **kwargs):
        self.log(logging.WARNING, event, **kwargs)
    
    def error(self, event: str, **kwargs):
        self.log(logging.ERROR, event, **kwargs)
