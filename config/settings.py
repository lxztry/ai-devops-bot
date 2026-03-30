"""Configuration management for AI Coding Demo"""
import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from functools import lru_cache


CONFIG_DIR = Path.home() / ".ai_coding_demo"
CONFIG_FILE = CONFIG_DIR / "config.json"

ENV_PREFIX = "AI_CODING_"


@dataclass
class GitConfig:
    name: str = ""
    email: str = ""
    token: str = ""
    
    @property
    def configured(self) -> bool:
        return bool(self.name and self.email and self.token)
    
    @classmethod
    def from_env(cls) -> "GitConfig":
        return cls(
            name=os.environ.get(f"{ENV_PREFIX}GIT_NAME", ""),
            email=os.environ.get(f"{ENV_PREFIX}GIT_EMAIL", ""),
            token=os.environ.get(f"{ENV_PREFIX}GITHUB_TOKEN", ""),
        )


@dataclass
class Preferences:
    preferred_languages: List[str] = field(default_factory=lambda: ["Python", "TypeScript", "JavaScript"])
    exclude_orgs: List[str] = field(default_factory=list)
    require_tests: bool = True
    auto_confirm_issue: bool = False
    max_complexity: str = "medium"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    
    @classmethod
    def from_env(cls) -> "Preferences":
        langs_str = os.environ.get(f"{ENV_PREFIX}PREFERRED_LANGUAGES", "")
        langs = [l.strip() for l in langs_str.split(",")] if langs_str else cls().preferred_languages
        
        exclude_str = os.environ.get(f"{ENV_PREFIX}EXCLUDE_ORGS", "")
        exclude_orgs = [o.strip() for o in exclude_str.split(",")] if exclude_str else []
        
        return cls(
            preferred_languages=langs,
            exclude_orgs=exclude_orgs,
            require_tests=os.environ.get(f"{ENV_PREFIX}REQUIRE_TESTS", "true").lower() == "true",
            auto_confirm_issue=os.environ.get(f"{ENV_PREFIX}AUTO_CONFIRM", "false").lower() == "true",
            max_complexity=os.environ.get(f"{ENV_PREFIX}MAX_COMPLEXITY", "medium"),
            llm_provider=os.environ.get(f"{ENV_PREFIX}LLM_PROVIDER", "openai"),
            llm_model=os.environ.get(f"{ENV_PREFIX}LLM_MODEL", "gpt-4"),
        )


@dataclass
class Paths:
    workspace: Path = field(default_factory=lambda: Path.home() / "ai_coding_workspace")
    logs: Path = field(default_factory=lambda: Path(__file__).parent.parent / "logs")
    
    def ensure(self):
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_env(cls) -> "Paths":
        return cls(
            workspace=Path(os.environ.get(f"{ENV_PREFIX}WORKSPACE", str(cls().workspace))),
            logs=Path(os.environ.get(f"{ENV_PREFIX}LOGS", str(cls().logs))),
        )


@dataclass
class Config:
    git: GitConfig = field(default_factory=GitConfig)
    prefs: Preferences = field(default_factory=Preferences)
    paths: Paths = field(default_factory=Paths)
    
    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
    
    @classmethod
    @lru_cache(maxsize=1)
    def load(cls) -> "Config":
        env_git = GitConfig.from_env()
        env_prefs = Preferences.from_env()
        env_paths = Paths.from_env()
        
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                file_git = GitConfig(**data.get("git", {}))
                file_prefs = Preferences(**data.get("prefs", {}))
                file_paths = Paths(**data.get("paths", {}))
                
                return cls(
                    git=GitConfig(
                        name=env_git.name or file_git.name,
                        email=env_git.email or file_git.email,
                        token=env_git.token or file_git.token,
                    ),
                    prefs=Preferences(
                        preferred_languages=env_prefs.preferred_languages or file_prefs.preferred_languages,
                        exclude_orgs=env_prefs.exclude_orgs or file_prefs.exclude_orgs,
                        require_tests=env_prefs.require_tests,
                        auto_confirm_issue=env_prefs.auto_confirm_issue,
                        max_complexity=env_prefs.max_complexity,
                        llm_provider=env_prefs.llm_provider,
                        llm_model=env_prefs.llm_model,
                    ),
                    paths=Paths(
                        workspace=env_paths.workspace or file_paths.workspace,
                        logs=env_paths.logs or file_paths.logs,
                    ),
                )
            except Exception:
                pass
        
        return cls(
            git=env_git,
            prefs=env_prefs,
            paths=env_paths,
        )
    
    def ensure_workspace(self):
        self.paths.ensure()
        return self.paths.workspace
    
    @classmethod
    def get_env_help(cls) -> str:
        return f"""
Environment Variables:
  {ENV_PREFIX}GIT_NAME              - Git user name
  {ENV_PREFIX}GIT_EMAIL             - Git email
  {ENV_PREFIX}GITHUB_TOKEN          - GitHub Personal Access Token
  {ENV_PREFIX}PREFERRED_LANGUAGES   - Comma-separated languages (e.g., "Python,TypeScript")
  {ENV_PREFIX}REQUIRE_TESTS         - Require tests (true/false)
  {ENV_PREFIX}AUTO_CONFIRM          - Auto confirm issue selection (true/false)
  {ENV_PREFIX}MAX_COMPLEXITY         - Max complexity (easy/medium/high)
  {ENV_PREFIX}WORKSPACE              - Workspace directory path
  {ENV_PREFIX}LOGS                   - Logs directory path
  {ENV_PREFIX}LLM_PROVIDER           - LLM provider (openai/anthropic)
  {ENV_PREFIX}LLM_MODEL             - LLM model name
"""


def setup_interactive():
    """Interactive configuration setup"""
    print("=" * 60)
    print("   AI Coding Demo - 配置向导")
    print("=" * 60)
    print()
    
    config = Config.load()
    
    print("📌 Git 配置")
    print("-" * 40)
    config.git.name = input(f"  Git 用户名 [{config.git.name}]: ").strip() or config.git.name
    config.git.email = input(f"  Git 邮箱 [{config.git.email}]: ").strip() or config.git.email
    
    token_input = input("  GitHub Token (留空手动配置): ").strip()
    if token_input:
        config.git.token = token_input
    
    print()
    print("💻 偏好设置")
    print("-" * 40)
    langs = input(f"  偏好语言 (逗号分隔) [{','.join(config.prefs.preferred_languages)}]: ").strip()
    if langs:
        config.prefs.preferred_languages = [l.strip() for l in langs.split(",")]
    
    tests = input(f"  必须有测试用例? (y/n) [{'y' if config.prefs.require_tests else 'n'}]: ").strip().lower()
    if tests == 'y':
        config.prefs.require_tests = True
    elif tests == 'n':
        config.prefs.require_tests = False
    
    print()
    print("📁 路径设置")
    print("-" * 40)
    workspace = input(f"  工作目录 [{config.paths.workspace}]: ").strip()
    if workspace:
        config.paths.workspace = Path(workspace)
    
    config.save()
    print()
    print("✅ 配置已保存!")
    print(f"   配置文件: {CONFIG_FILE}")
    print()


def check_config(config: Config) -> tuple[bool, List[str]]:
    """Check if configuration is complete, return (is_ok, missing_items)"""
    missing = []
    
    if not config.git.name:
        missing.append("Git 用户名")
    if not config.git.email:
        missing.append("Git 邮箱")
    if not config.git.token:
        missing.append("GitHub Token")
    
    return len(missing) == 0, missing


def print_config_status(config: Config):
    """Print current configuration status"""
    print("📋 当前配置状态:")
    print(f"   Git 用户: {config.git.name or '❌ 未配置'}")
    print(f"   Git 邮箱: {config.git.email or '❌ 未配置'}")
    print(f"   GitHub Token: {'✅ 已配置' if config.git.token else '❌ 未配置'}")
    print(f"   偏好语言: {', '.join(config.prefs.preferred_languages)}")
    print(f"   工作目录: {config.paths.workspace}")
    print()


def main():
    """Main entry point for config command"""
    import argparse
    parser = argparse.ArgumentParser(description="AI Coding Demo Configuration")
    parser.add_argument("--show-env", action="store_true", help="Show environment variable configuration")
    parser.add_argument("--reset", action="store_true", help="Reset configuration to defaults")
    
    args = parser.parse_args()
    
    if args.show_env:
        print(Config.get_env_help())
        return
    
    if args.reset:
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
            print("Configuration reset to defaults.")
        return
    
    setup_interactive()


if __name__ == "__main__":
    main()
