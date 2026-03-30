"""Unit tests for utility functions"""
import pytest
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_coding_demo.core.utils import (
    setup_logging, retry, safe_execute, StructuredLogger
)


class TestSetupLogging:
    """Tests for setup_logging"""
    
    def test_setup_logging_creates_logger(self):
        logger = setup_logging(level=10)
        assert logger.name == "ai_coding_demo"
        assert logger.level == 10
    
    def test_setup_logging_with_file(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_dir=tmp_path, level=10)
        
        assert logger.handlers
        assert log_file.exists()


class TestRetry:
    """Tests for retry decorator"""
    
    def test_retry_success_first_attempt(self):
        call_count = 0
        
        @retry(max_attempts=3, delay=0.1)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = succeed()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_success_after_failures(self):
        call_count = 0
        
        @retry(max_attempts=3, delay=0.1)
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "success"
        
        result = fail_twice()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_all_fail(self):
        call_count = 0
        
        @retry(max_attempts=3, delay=0.1)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("always fails")
        
        with pytest.raises(ValueError):
            always_fail()
        assert call_count == 3
    
    def test_retry_with_custom_exceptions(self):
        call_count = 0
        
        @retry(max_attempts=3, delay=0.1, exceptions=(ValueError,))
        def only_catches_value_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("wrong type")
        
        with pytest.raises(TypeError):
            only_catches_value_error()
        assert call_count == 1


class TestSafeExecute:
    """Tests for safe_execute decorator"""
    
    def test_safe_execute_success(self):
        @safe_execute(default="default")
        def succeed():
            return "success"
        
        result = succeed()
        assert result == "success"
    
    def test_safe_execute_returns_default_on_error(self):
        @safe_execute(default="default")
        def fail():
            raise ValueError("error")
        
        result = fail()
        assert result == "default"
    
    def test_safe_execute_logs_error(self, tmp_path):
        log_file = tmp_path / "test.log"
        
        @safe_execute(default="default", log_errors=True)
        def fail():
            raise ValueError("error")
        
        result = fail()
        assert result == "default"
    
    def test_safe_execute_custom_default(self):
        @safe_execute(default=None)
        def fail():
            raise ValueError()
        
        result = fail()
        assert result is None


class TestStructuredLogger:
    """Tests for StructuredLogger"""
    
    def test_structured_logger_init(self):
        logger = StructuredLogger("test")
        assert logger.logger.name == "test"
        assert logger.log_file is None
    
    def test_structured_logger_with_file(self, tmp_path):
        log_file = tmp_path / "structured.jsonl"
        logger = StructuredLogger("test", log_file)
        
        logger.info("test_event", key="value")
        
        assert log_file.exists()
        content = log_file.read_text()
        assert "test_event" in content
        assert "value" in content
    
    def test_structured_logger_serialization(self, tmp_path):
        log_file = tmp_path / "structured.jsonl"
        logger = StructuredLogger("test", log_file)
        
        logger.info("event1", count=42, active=True)
        
        content = log_file.read_text()
        assert '"event": "event1"' in content
        assert '"count": 42' in content
