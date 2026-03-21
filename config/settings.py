"""Configuration management for AI Coding Demo"""
import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List
import shutil


CONFIG_DIR = Path.home() / ".ai_coding_demo"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class GitConfig:
    name: str = ""
    email: str = ""
    token: str = ""
    
    @property
    def configured(self) -> bool:
        return bool(self.name and self.email and self.token)


@dataclass
class Preferences:
    preferred_languages: List[str] = field(default_factory=lambda: ["Python", "TypeScript", "JavaScript"])
    exclude_orgs: List[str] = field(default_factory=list)
    require_tests: bool = True
    auto_confirm_issue: bool = False
    max_complexity: str = "medium"


@dataclass
class Paths:
    workspace: Path = field(default_factory=lambda: Path.home() / "ai_coding_workspace")
    logs: Path = field(default_factory=lambda: Path(__file__).parent.parent / "logs")
    
    def ensure(self):
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)


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
    def load(cls) -> "Config":
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                return cls(
                    git=GitConfig(**data.get("git", {})),
                    prefs=Preferences(**data.get("prefs", {})),
                    paths=Paths(**data.get("paths", {})),
                )
            except Exception:
                pass
        return cls()
    
    def ensure_workspace(self):
        self.paths.ensure()
        return self.paths.workspace


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


if __name__ == "__main__":
    setup_interactive()
