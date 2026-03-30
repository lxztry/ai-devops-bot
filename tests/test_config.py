"""Unit tests for configuration management"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_coding_demo.config.settings import (
    Config, GitConfig, Preferences, Paths, 
    ENV_PREFIX, check_config
)


class TestGitConfig:
    """Tests for GitConfig"""
    
    def test_git_config_default(self):
        config = GitConfig()
        assert config.name == ""
        assert config.email == ""
        assert config.token == ""
        assert not config.configured
    
    def test_git_config_with_values(self):
        config = GitConfig(name="test", email="test@test.com", token="abc123")
        assert config.name == "test"
        assert config.email == "test@test.com"
        assert config.token == "abc123"
        assert config.configured
    
    def test_git_config_from_env(self):
        with patch.dict(os.environ, {
            f"{ENV_PREFIX}GIT_NAME": "env_user",
            f"{ENV_PREFIX}GIT_EMAIL": "env@test.com",
            f"{ENV_PREFIX}GITHUB_TOKEN": "env_token"
        }):
            config = GitConfig.from_env()
            assert config.name == "env_user"
            assert config.email == "env@test.com"
            assert config.token == "env_token"
    
    def test_git_config_partial_env(self):
        with patch.dict(os.environ, {
            f"{ENV_PREFIX}GIT_NAME": "env_user"
        }, clear=False):
            config = GitConfig.from_env()
            assert config.name == "env_user"
            assert config.email == ""


class TestPreferences:
    """Tests for Preferences"""
    
    def test_preferences_default(self):
        prefs = Preferences()
        assert prefs.preferred_languages == ["Python", "TypeScript", "JavaScript"]
        assert prefs.require_tests is True
        assert prefs.auto_confirm_issue is False
        assert prefs.max_complexity == "medium"
    
    def test_preferences_from_env(self):
        with patch.dict(os.environ, {
            f"{ENV_PREFIX}PREFERRED_LANGUAGES": "Go,Rust,Python",
            f"{ENV_PREFIX}REQUIRE_TESTS": "false",
            f"{ENV_PREFIX}AUTO_CONFIRM": "true",
            f"{ENV_PREFIX}MAX_COMPLEXITY": "high",
            f"{ENV_PREFIX}LLM_PROVIDER": "anthropic",
            f"{ENV_PREFIX}LLM_MODEL": "claude-3"
        }):
            prefs = Preferences.from_env()
            assert prefs.preferred_languages == ["Go", "Rust", "Python"]
            assert prefs.require_tests is False
            assert prefs.auto_confirm_issue is True
            assert prefs.max_complexity == "high"
            assert prefs.llm_provider == "anthropic"
            assert prefs.llm_model == "claude-3"


class TestPaths:
    """Tests for Paths"""
    
    def test_paths_default(self):
        paths = Paths()
        assert paths.workspace == Path.home() / "ai_coding_workspace"
        assert "ai_coding_demo" in str(paths.logs)
    
    def test_paths_ensure_creates_directories(self, tmp_path):
        paths = Paths(workspace=tmp_path / "workspace", logs=tmp_path / "logs")
        paths.ensure()
        assert paths.workspace.exists()
        assert paths.logs.exists()
    
    def test_paths_from_env(self, tmp_path):
        with patch.dict(os.environ, {
            f"{ENV_PREFIX}WORKSPACE": str(tmp_path / "custom_workspace"),
            f"{ENV_PREFIX}LOGS": str(tmp_path / "custom_logs")
        }):
            paths = Paths.from_env()
            assert paths.workspace == tmp_path / "custom_workspace"
            assert paths.logs == tmp_path / "custom_logs"


class TestConfig:
    """Tests for Config"""
    
    def test_config_default(self):
        config = Config()
        assert isinstance(config.git, GitConfig)
        assert isinstance(config.prefs, Preferences)
        assert isinstance(config.paths, Paths)
    
    def test_config_save_load(self, tmp_path):
        config = Config(
            git=GitConfig(name="test", email="test@test.com", token="abc"),
            prefs=Preferences(preferred_languages=["Python"]),
            paths=Paths(workspace=tmp_path / "ws", logs=tmp_path / "logs")
        )
        config.save()
        
        loaded = Config.load()
        assert loaded.git.name == "test"
        assert loaded.git.email == "test@test.com"
        assert loaded.prefs.preferred_languages == ["Python"]
    
    def test_config_env_overrides_file(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text('{"git": {"name": "file_user"}, "prefs": {"preferred_languages": ["Java"]}, "paths": {}}')
        
        with patch("ai_coding_demo.config.settings.CONFIG_FILE", config_file):
            with patch.dict(os.environ, {
                f"{ENV_PREFIX}GIT_NAME": "env_user"
            }):
                loaded = Config.load()
                assert loaded.git.name == "env_user"


class TestCheckConfig:
    """Tests for check_config function"""
    
    def test_check_config_complete(self):
        config = Config(
            git=GitConfig(name="test", email="test@test.com", token="abc")
        )
        is_valid, missing = check_config(config)
        assert is_valid
        assert missing == []
    
    def test_check_config_missing_name(self):
        config = Config(
            git=GitConfig(name="", email="test@test.com", token="abc")
        )
        is_valid, missing = check_config(config)
        assert not is_valid
        assert "Git 用户名" in missing
    
    def test_check_config_missing_email(self):
        config = Config(
            git=GitConfig(name="test", email="", token="abc")
        )
        is_valid, missing = check_config(config)
        assert not is_valid
        assert "Git 邮箱" in missing
    
    def test_check_config_missing_token(self):
        config = Config(
            git=GitConfig(name="test", email="test@test.com", token="")
        )
        is_valid, missing = check_config(config)
        assert not is_valid
        assert "GitHub Token" in missing
