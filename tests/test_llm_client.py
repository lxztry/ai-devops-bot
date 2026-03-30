"""Unit tests for LLM client"""
import pytest
from unittest.mock import patch, MagicMock

from ai_coding_demo.core.llm_client import (
    MockLLMClient, OpenAIClient, AnthropicClient, get_llm_client,
    generate_code_prompt, generate_test_prompt
)


class TestMockLLMClient:
    """Tests for MockLLMClient"""
    
    def test_mock_client_available(self):
        client = MockLLMClient()
        assert client.is_available() is True
    
    def test_mock_client_generate(self):
        client = MockLLMClient()
        response = client.generate("test prompt")
        
        assert response.content.startswith("# Mock implementation")
        assert response.model == "mock"
        assert response.finish_reason == "stop"


class TestOpenAIClient:
    """Tests for OpenAIClient"""
    
    def test_openai_client_no_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            client = OpenAIClient()
            assert client.is_available() is False
    
    def test_openai_client_with_api_key(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test_key"}):
            client = OpenAIClient(api_key="test_key")
            assert client.api_key == "test_key"


class TestAnthropicClient:
    """Tests for AnthropicClient"""
    
    def test_anthropic_client_no_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            client = AnthropicClient()
            assert client.is_available() is False
    
    def test_anthropic_client_with_api_key(self):
        client = AnthropicClient(api_key="test_key")
        assert client.api_key == "test_key"


class TestGetLLMClient:
    """Tests for get_llm_client factory"""
    
    def test_get_llm_client_mock(self):
        client = get_llm_client("mock")
        assert isinstance(client, MockLLMClient)
    
    def test_get_llm_client_fallback(self):
        with patch.dict("os.environ", {}, clear=True):
            client = get_llm_client("unknown_provider")
            assert isinstance(client, MockLLMClient)


class TestPromptGeneration:
    """Tests for prompt generation functions"""
    
    def test_generate_code_prompt(self):
        prompt = generate_code_prompt(
            issue_title="Fix bug",
            issue_body="There is a bug in the login function",
            file_path="src/auth.py",
            file_content="def login():\n    pass",
            language="python"
        )
        
        assert "Fix bug" in prompt
        assert "src/auth.py" in prompt
        assert "def login():" in prompt
        assert "python" in prompt
    
    def test_generate_test_prompt(self):
        prompt = generate_test_prompt(
            issue_title="Add tests",
            issue_body="Add unit tests for auth module",
            target_files=["src/auth.py", "src/user.py"],
            language="python"
        )
        
        assert "Add tests" in prompt
        assert "src/auth.py" in prompt
        assert "python" in prompt
