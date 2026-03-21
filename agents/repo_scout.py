"""GitHub Issue Discovery Agent"""
import json
import subprocess
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class GitHubIssue:
    repo: str
    number: int
    title: str
    body: str
    labels: List[str]
    state: str
    assignee: Optional[str]
    comments: int
    url: str
    created_at: str
    
    @property
    def difficulty(self) -> str:
        """Infer difficulty from labels"""
        label_str = " ".join(self.labels).lower()
        if any(l in label_str for l in ["good first issue", "beginner", "easy"]):
            return "easy"
        elif any(l in label_str for l in ["hard", "complex", "expert"]):
            return "hard"
        return "medium"
    
    def __str__(self) -> str:
        labels_str = ", ".join(f"[{l}]" for l in self.labels[:5])
        return f"""
┌─────────────────────────────────────────────────────────┐
│ #{self.number} | {self.repo}                                    │
├─────────────────────────────────────────────────────────┤
│ 标题: {self.title[:50]}...                                  │
│ 难度: {self.difficulty:8} | 状态: {self.state} | 评论: {self.comments}       │
│ 标签: {labels_str}               │
│ 链接: {self.url[:60]}...                        │
└─────────────────────────────────────────────────────────┘"""


class RepoScoutAgent:
    """Scout GitHub for suitable issues to implement"""
    
    def __init__(self, token: str, preferences: dict):
        self.token = token
        self.preferences = preferences
        self._gh_available = None
    
    @property
    def gh_available(self) -> bool:
        if self._gh_available is None:
            try:
                subprocess.run(["gh", "--version"], capture_output=True, check=True)
                self._gh_available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                self._gh_available = False
        return self._gh_available
    
    def search_issues(self, language: Optional[str] = None, limit: int = 10) -> List[GitHubIssue]:
        """Search GitHub for suitable issues"""
        languages = [language] if language else self.preferences.get("preferred_languages", [])
        results = []
        
        for lang in languages[:2]:
            issues = self._search_by_language(lang, limit // len(languages))
            results.extend(issues)
        
        results = [r for r in results if r.assignee is None]
        return sorted(results, key=lambda x: x.comments, reverse=True)[:limit]
    
    def _search_by_language(self, language: str, limit: int) -> List[GitHubIssue]:
        """Search issues for a specific language"""
        query_parts = [
            "is:issue",
            "is:open",
            "no:assignee",
            f"language:{language}",
        ]
        
        if self.preferences.get("require_tests", True):
            query_parts.append("label:has-tests")
        
        query = " ".join(query_parts)
        
        if self.gh_available:
            return self._search_gh_cli(query, limit)
        else:
            return self._search_gh_api(query, limit)
    
    def _search_gh_cli(self, query: str, limit: int) -> List[GitHubIssue]:
        """Search using gh CLI"""
        try:
            cmd = [
                "gh", "issue", "list",
                "--limit", str(limit),
                "--json", "number,title,body,labels,state,assignee,commentsCount,url,createdAt,repository"
            ]
            env = {"GH_TOKEN": self.token} if self.token else {}
            import os as os_module
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env={**os_module.environ, **env}
            )
            
            if result.returncode != 0:
                return []
            
            data = json.loads(result.stdout)
            return [self._parse_gh_output(item) for item in data]
        except Exception as e:
            print(f"gh CLI error: {e}")
            return []
    
    def _search_gh_api(self, query: str, limit: int) -> List[GitHubIssue]:
        """Search using GitHub REST API"""
        import urllib.request
        import urllib.parse
        
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.github.com/search/issues?q={encoded_query}&per_page={limit}&sort=comments"
        
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github.v3+json")
        if self.token:
            req.add_header("Authorization", f"token {self.token}")
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())
                return [self._parse_api_output(item) for item in data.get("items", [])]
        except Exception as e:
            print(f"GitHub API error: {e}")
            return []
    
    def _parse_gh_output(self, item: dict) -> GitHubIssue:
        """Parse gh CLI output"""
        repo = item.get("repository", {}).get("nameWithOwner", "unknown")
        return GitHubIssue(
            repo=repo,
            number=item["number"],
            title=item["title"],
            body=item.get("body", ""),
            labels=[l["name"] for l in item.get("labels", [])],
            state=item["state"],
            assignee=item.get("assignee", {}).get("login") if item.get("assignee") else None,
            comments=item.get("commentsCount", 0),
            url=item["url"],
            created_at=item["createdAt"],
        )
    
    def _parse_api_output(self, item: dict) -> GitHubIssue:
        """Parse GitHub API output"""
        repo_url = item.get("repository_url", "")
        repo = repo_url.split("/")[-2:] if repo_url else "unknown/unknown"
        
        return GitHubIssue(
            repo="/".join(repo) if len(repo) == 2 else "unknown/unknown",
            number=item["number"],
            title=item["title"],
            body=item.get("body", ""),
            labels=[l["name"] for l in item.get("labels", [])],
            state=item["state"],
            assignee=item.get("assignee", {}).get("login") if item.get("assignee") else None,
            comments=item.get("comments", 0),
            url=item["html_url"],
            created_at=item["created_at"],
        )
    
    def select_random(self, issues: List[GitHubIssue]) -> Optional[GitHubIssue]:
        """Randomly select an issue"""
        import random
        if issues:
            return random.choice(issues)
        return None
    
    def filter_by_complexity(self, issues: List[GitHubIssue], max_complexity: str = "medium") -> List[GitHubIssue]:
        """Filter issues by complexity"""
        if max_complexity == "easy":
            return [i for i in issues if i.difficulty in ["easy", "medium"]]
        elif max_complexity == "medium":
            return issues
        return issues
