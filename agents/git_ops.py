"""Git Operations Agent"""
import os
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class GitOperationResult:
    success: bool
    message: str
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    remote_url: Optional[str] = None


class GitOpsAgent:
    """Handle all Git operations"""
    
    def __init__(self, repo_path: Path, git_config: dict):
        self.repo_path = Path(repo_path)
        self.git_config = git_config
        self._setup_git_config()
    
    def _setup_git_config(self):
        """Configure git user for this repo"""
        try:
            subprocess.run(
                ["git", "config", "user.name", self.git_config.get("name", "AI Assistant")],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            subprocess.run(
                ["git", "config", "user.email", self.git_config.get("email", "ai@example.com")],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not set git config: {e}")
    
    def get_current_branch(self) -> str:
        """Get current branch name"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return "main"
    
    def get_remote_url(self) -> Optional[str]:
        """Get remote URL"""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return None
    
    def list_branches(self, remote: bool = False) -> List[str]:
        """List local or remote branches"""
        try:
            cmd = ["git", "branch"]
            if remote:
                cmd.append("-r")
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            branches = [b.strip().replace("* ", "") for b in result.stdout.split("\n") if b]
            return branches
        except:
            return []
    
    def create_branch(self, branch_name: str) -> GitOperationResult:
        """Create a new feature branch"""
        sanitized = self._sanitize_branch_name(branch_name)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        full_branch = f"ai-demo/{sanitized}-{timestamp}"
        
        try:
            subprocess.run(
                ["git", "checkout", "-b", full_branch],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            return GitOperationResult(
                success=True,
                message=f"Created and switched to branch: {full_branch}",
                branch=full_branch
            )
        except subprocess.CalledProcessError as e:
            return GitOperationResult(
                success=False,
                message=f"Failed to create branch: {e.stderr.decode() if e.stderr else str(e)}"
            )
    
    def _sanitize_branch_name(self, name: str) -> str:
        """Sanitize string to be a valid git branch name"""
        name = name.lower()
        name = re.sub(r"[^a-z0-9\s-]", "", name)
        name = re.sub(r"[\s]+", "-", name)
        name = name[:50]
        return name or "feature"
    
    def stage_all(self) -> GitOperationResult:
        """Stage all changes"""
        try:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            return GitOperationResult(success=True, message="All changes staged")
        except subprocess.CalledProcessError as e:
            return GitOperationResult(success=False, message=f"Failed to stage: {str(e)}")
    
    def commit(self, message: str) -> GitOperationResult:
        """Commit staged changes"""
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commit_hash = self.get_last_commit_hash()
            
            return GitOperationResult(
                success=True,
                message=f"Committed: {message}",
                commit_hash=commit_hash
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            if "nothing to commit" in error_msg.lower():
                return GitOperationResult(success=True, message="Nothing to commit")
            return GitOperationResult(success=False, message=f"Commit failed: {error_msg}")
    
    def get_last_commit_hash(self, short: bool = True) -> Optional[str]:
        """Get last commit hash"""
        try:
            cmd = ["git", "rev-parse", "HEAD"]
            if short:
                cmd.append("--short")
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except:
            return None
    
    def get_status(self) -> str:
        """Get git status"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip() if result.stdout else "Clean"
        except:
            return "Error getting status"
    
    def push(self, branch: Optional[str] = None, set_upstream: bool = True) -> GitOperationResult:
        """Push branch to remote"""
        if not branch:
            branch = self.get_current_branch()
        
        try:
            cmd = ["git", "push"]
            if set_upstream:
                cmd.extend(["-u", "origin", branch])
            else:
                cmd.extend(["origin", branch])
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return GitOperationResult(
                    success=True,
                    message=f"Pushed to origin/{branch}",
                    branch=branch
                )
            else:
                return GitOperationResult(
                    success=False,
                    message=f"Push failed: {result.stderr}"
                )
        except subprocess.TimeoutExpired:
            return GitOperationResult(success=False, message="Push timeout")
        except Exception as e:
            return GitOperationResult(success=False, message=f"Push error: {str(e)}")
    
    def create_pr(self, title: str, body: str, token: str) -> GitOperationResult:
        """Create a pull request using gh CLI"""
        branch = self.get_current_branch()
        
        try:
            cmd = [
                "gh", "pr", "create",
                "--title", title,
                "--body", body,
                "--assignee", "@me"
            ]
            
            env = {"GH_TOKEN": token} if token else {}
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                env={**os.environ, **env} if token else None
            )
            
            if result.returncode == 0:
                pr_url = result.stdout.strip() if result.stdout else "Created"
                return GitOperationResult(
                    success=True,
                    message=f"PR created: {pr_url}",
                    branch=branch
                )
            else:
                return GitOperationResult(
                    success=False,
                    message=f"PR creation failed: {result.stderr}"
                )
        except FileNotFoundError:
            return GitOperationResult(
                success=False,
                message="gh CLI not found. Please install GitHub CLI."
            )
        except Exception as e:
            return GitOperationResult(success=False, message=f"PR error: {str(e)}")
    
    def checkout_main(self) -> GitOperationResult:
        """Switch back to main branch"""
        try:
            main_branch = self._find_main_branch()
            subprocess.run(
                ["git", "checkout", main_branch],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )
            return GitOperationResult(
                success=True,
                message=f"Switched to {main_branch}",
                branch=main_branch
            )
        except subprocess.CalledProcessError as e:
            return GitOperationResult(success=False, message=f"Checkout failed: {str(e)}")
    
    def _find_main_branch(self) -> str:
        """Find the main branch name"""
        for name in ["main", "master", "develop"]:
            if name in self.list_branches():
                return name
        return "main"
