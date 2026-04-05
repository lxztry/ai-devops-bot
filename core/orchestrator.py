"""Master Orchestrator - Coordinates all agents"""
import sys
import time
import logging
from pathlib import Path
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai_coding_demo.config.settings import Config, check_config
from ai_coding_demo.core.utils import setup_logging, StructuredLogger
from ai_coding_demo.agents.repo_scout import RepoScoutAgent, GitHubIssue
from ai_coding_demo.agents.code_explorer import CodeExplorerAgent, RepoAnalysis
from ai_coding_demo.agents.dev_env import DevEnvAgent
from ai_coding_demo.agents.git_ops import GitOpsAgent
from ai_coding_demo.agents.docs_logger import DocsLogger
from ai_coding_demo.agents.implementation import ImplementationAgent, ImplementationPlan, ImplementationResult


class MasterOrchestrator:
    """Coordinates all agents to execute AI coding demo end-to-end"""
    
    def __init__(self, config: Config, parallel: bool = True):
        self.config = config
        self.workspace = config.ensure_workspace()
        self.logger = DocsLogger(config.paths.logs)
        self.log = setup_logging(config.paths.logs)
        self.struct_log = StructuredLogger("ai_coding_demo", config.paths.logs / "structured.jsonl")
        self.parallel = parallel
        
        self.issue: Optional[GitHubIssue] = None
        self.analysis: Optional[RepoAnalysis] = None
        self.plan: Optional[ImplementationPlan] = None
        self.result: Optional[ImplementationResult] = None
        self.git_agent: Optional[GitOpsAgent] = None
    
    def run(self, interactive: bool = True) -> bool:
        """Run the complete AI coding demo"""
        print("=" * 60)
        print("   AI Coding Demo Assistant")
        print("=" * 60)
        print()
        
        is_valid, missing = check_config(self.config)
        if not is_valid:
            print(f"Configuration incomplete. Please run: python -m ai_coding_demo.config.settings")
            return False
        
        print(f"Workspace: {self.workspace}")
        print()
        
        session = self.logger.start_session()
        
        step = self.logger.start_step("Step 1: 发现需求")
        print("Step 1: 发现 GitHub Issue...")
        
        self.issue = self._discover_issue(interactive)
        if not self.issue:
            self.logger.end_step(step, "failed", error="No issue selected")
            return False
        
        session.issue_url = self.issue.url
        session.issue_title = self.issue.title
        
        self.logger.end_step(step, "success", details={
            "issue": f"#{self.issue.number} {self.issue.title}",
            "repo": self.issue.repo,
            "difficulty": self.issue.difficulty,
        })
        
        step = self.logger.start_step("Step 2: 理解代码")
        print("\nStep 2: 理解代码仓库...")
        
        self.analysis = self._analyze_repo(self.issue.repo)
        if not self.analysis:
            self.logger.end_step(step, "failed", error="Failed to analyze repo")
            return False
        
        if self.config.prefs.use_ast_analysis:
            print("   (Using AST-based analysis)")
        
        self.logger.end_step(step, "success", details={
            "language": self.analysis.language,
            "files": len(self.analysis.files),
            "tests": len(self.analysis.test_files),
        })
        
        step = self.logger.start_step("Step 3: 创建分支")
        print("\nStep 3: 创建功能分支...")
        
        git_agent = GitOpsAgent(self.analysis.local_path, {
            "name": self.config.git.name,
            "email": self.config.git.email,
        })
        
        branch_result = git_agent.create_branch(self.issue.title)
        if not branch_result.success:
            self.logger.end_step(step, "failed", error=branch_result.message)
            return False
        
        session.branch_name = branch_result.branch or ""
        
        self.logger.end_step(step, "success", details={
            "branch": branch_result.branch,
        })
        
        step = self.logger.start_step("Step 4: 配置环境")
        print("\nStep 4: 配置开发环境...")
        
        env_result = None
        impl_result = None
        
        if self.parallel:
            env_result, impl_result = self._run_parallel_steps()
        else:
            dev_env = DevEnvAgent(self.analysis.local_path)
            env_result = dev_env.setup()
            
            impl_agent = ImplementationAgent(
                self.analysis.local_path, 
                self.analysis,
                llm_provider=self.config.prefs.llm_provider,
                llm_model=self.config.prefs.llm_model
            )
            self.plan = impl_agent.create_implementation_plan(self.issue.body, self.issue.title)
            impl_result = impl_agent.implement(self.plan, self.issue.title, self.issue.body)
        
        env_success = env_result.success if env_result else False
        self.result = impl_result
        
        self.logger.end_step(step, "success" if env_success else "warning", details={
            "runtime": env_result.runtime if env_result else "N/A",
            "installed": env_result.installed_deps if env_result else [],
            "test_result": env_result.test_result if env_result else "N/A",
        })
        
        step = self.logger.start_step("Step 5: 实现功能")
        print("\nStep 5: 实现代码变更...")
        
        plan_approach = self.plan.approach if self.plan else "N/A"
        plan_complexity = self.plan.estimated_complexity if self.plan else "N/A"
        
        result_success = self.result.success if self.result else False
        result_files = self.result.files_modified if self.result else []
        result_tests = self.result.test_results if self.result else "N/A"
        
        self.logger.end_step(step, "success" if result_success else "warning", details={
            "approach": plan_approach,
            "complexity": plan_complexity,
            "files_modified": result_files,
            "test_results": result_tests,
        })
        
        step = self.logger.start_step("Step 6: 提交代码")
        print("\nStep 6: 提交代码...")
        
        git_agent.stage_all()
        status = git_agent.get_status()
        
        commit_message = f"feat: implement {self.issue.title}\n\n"
        commit_message += f"Closes #{self.issue.number}\n"
        commit_message += f"Repo: {self.issue.repo}\n"
        commit_message += f"Generated by AI Coding Demo"
        
        commit_result = git_agent.commit(commit_message)
        
        self.logger.end_step(step, "success", details={
            "commit": commit_result.commit_hash or "N/A",
            "status": status[:100],
        })
        
        step = self.logger.start_step("Step 7: 推送分支")
        print("\nStep 7: 推送分支...")
        
        push_result = git_agent.push()
        
        self.logger.end_step(step, "success" if push_result.success else "warning", details={
            "message": push_result.message,
        })
        
        pr_url = None
        if push_result.success:
            step = self.logger.start_step("Step 8: 创建 PR")
            print("\nStep 8: 创建 Pull Request...")
            
            pr_body = self.logger.generate_pr_description(session)
            pr_result = git_agent.create_pr(
                title=f"AI Demo: {self.issue.title}",
                body=pr_body,
                token=self.config.git.token,
            )
            
            pr_url = pr_result.message if pr_result.success else None
            
            self.logger.end_step(step, "success" if pr_result.success else "warning", details={
                "pr_url": pr_url or "N/A",
            })
        
        self.logger.end_session(pr_url)
        
        print("\n" + "=" * 60)
        print("   AI Coding Demo Complete!")
        print("=" * 60)
        
        return True
    
    def _discover_issue(self, interactive: bool = True) -> Optional[GitHubIssue]:
        """Discover and select a GitHub issue"""
        scout = RepoScoutAgent(
            token=self.config.git.token,
            preferences={
                "preferred_languages": self.config.prefs.preferred_languages,
                "require_tests": self.config.prefs.require_tests,
            }
        )
        
        print("Searching GitHub Issues...")
        issues = scout.search_issues(limit=10)
        
        if not issues:
            print("No suitable issues found, trying broader search...")
            issues = scout.search_issues(limit=5)
        
        if not issues:
            return None
        
        print(f"\nFound {len(issues)} candidate issues:\n")
        for i, issue in enumerate(issues[:5], 1):
            print(f"{i}. {issue}")
        
        if interactive:
            print("\n[Press Enter to randomly select, or enter a number]: ", end="")
            choice = input().strip()
            
            if choice == "":
                selected = scout.select_random(issues)
            else:
                try:
                    idx = int(choice) - 1
                    selected = issues[idx] if 0 <= idx < len(issues) else issues[0]
                except ValueError:
                    selected = issues[0]
        else:
            selected = scout.select_random(issues)
        
        if selected:
            print(f"\nSelected: #{selected.number} - {selected.title}")
        return selected
    
    def _analyze_repo(self, repo_full_name: str) -> Optional[RepoAnalysis]:
        """Clone and analyze repository"""
        explorer = CodeExplorerAgent(self.workspace)
        
        repo_url = f"https://github.com/{repo_full_name}.git"
        repo_name = self._extract_repo_name(repo_url)
        
        try:
            if self.config.prefs.use_ast_analysis:
                analysis = explorer.clone_and_analyze(repo_url)
                if analysis and analysis.files:
                    analysis = explorer.analyze_with_ast(analysis.local_path, repo_url)
            else:
                analysis = explorer.clone_and_analyze(repo_url)
            
            if analysis:
                print(f"\n{analysis.structure_summary}")
                self.log.info(f"Repository analysis complete: {repo_full_name}")
            return analysis
        except Exception as e:
            self.log.error(f"Repository analysis failed: {e}")
            return None
    
    def _extract_repo_name(self, url: str) -> str:
        """Extract repository name from URL"""
        if "/" in url:
            parts = url.rstrip("/").split("/")
            name = parts[-1]
            if name.endswith(".git"):
                name = name[:-4]
            return name
        return url
    
    def run_demo_mode(self):
        """Run a quick demo with minimal interaction"""
        print("Demo Mode - Quick demonstration")
        print("-" * 40)
        
        self.config.prefs.auto_confirm_issue = True
        
        return self.run(interactive=False)
    
    def _run_parallel_steps(self) -> Tuple:
        """Run environment setup and implementation in parallel"""
        if not self.analysis or not self.issue:
            return None, None
            
        dev_env = DevEnvAgent(self.analysis.local_path)
        impl_agent = ImplementationAgent(
            self.analysis.local_path, 
            self.analysis,
            llm_provider=self.config.prefs.llm_provider,
            llm_model=self.config.prefs.llm_model
        )
        
        issue_body = self.issue.body or ""
        issue_title = self.issue.title or ""
        
        self.plan = impl_agent.create_implementation_plan(issue_body, issue_title)
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            env_future = executor.submit(dev_env.setup)
            impl_future = executor.submit(
                impl_agent.implement, 
                self.plan, 
                issue_title, 
                issue_body
            )
            
            env_result = env_future.result()
            impl_result = impl_future.result()
        
        return env_result, impl_result
