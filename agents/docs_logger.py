"""Documentation and Logging Agent"""
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class StepLog:
    step_name: str
    start_time: str
    end_time: str
    duration_seconds: float
    status: str
    details: Dict = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ExecutionLog:
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    issue_url: str = ""
    issue_title: str = ""
    repo_url: str = ""
    branch_name: str = ""
    pr_url: Optional[str] = None
    steps: List[StepLog] = field(default_factory=list)
    summary: str = ""
    total_duration: float = 0.0
    
    def add_step(self, step: StepLog):
        self.steps.append(step)
    
    def finalize(self, pr_url: Optional[str] = None):
        self.end_time = datetime.now().isoformat()
        self.pr_url = pr_url
        self.total_duration = sum(s.duration_seconds for s in self.steps)
        self._generate_summary()
    
    def _generate_summary(self):
        """Generate execution summary"""
        step_summary = "\n".join([
            f"  - {s.step_name}: {s.status} ({s.duration_seconds:.1f}s)"
            for s in self.steps
        ])
        self.summary = f"""
═══════════════════════════════════════════════════════
                  AI Coding Demo - 执行摘要
═══════════════════════════════════════════════════════

📋 需求信息
   标题: {self.issue_title}
   链接: {self.issue_url}

📦 代码仓库
   仓库: {self.repo_url}
   分支: {self.branch_name}

🔧 执行步骤
{step_summary}

⏱️  总耗时: {self.total_duration:.1f} 秒

🔗 PR 链接: {self.pr_url or '未创建'}

═══════════════════════════════════════════════════════
"""


class DocsLogger:
    """Generate documentation and maintain execution logs"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"session_{self.session_id}.json"
        self.current_log: Optional[ExecutionLog] = None
    
    def start_session(self, issue_url: str = "", issue_title: str = "", repo_url: str = "") -> ExecutionLog:
        """Start a new execution session"""
        self.current_log = ExecutionLog(
            session_id=self.session_id,
            start_time=datetime.now().isoformat(),
            issue_url=issue_url,
            issue_title=issue_title,
            repo_url=repo_url,
        )
        return self.current_log
    
    def start_step(self, step_name: str) -> StepLog:
        """Start tracking a new step"""
        return StepLog(
            step_name=step_name,
            start_time=datetime.now().isoformat(),
            end_time="",
            duration_seconds=0.0,
            status="in_progress",
        )
    
    def end_step(self, step: StepLog, status: str = "success", details: Optional[Dict] = None, error: Optional[str] = None):  # type: ignore
        """End tracking a step"""
        end_time = datetime.now()
        start_dt = datetime.fromisoformat(step.start_time)
        step.end_time = end_time.isoformat()
        step.duration_seconds = (end_time - start_dt).total_seconds()
        step.status = status
        if details:
            step.details = details
        if error:
            step.error = error
        
        if self.current_log:
            self.current_log.add_step(step)
        self._save_log()
    
    def end_session(self, pr_url: Optional[str] = None):
        """End the current session"""
        if self.current_log:
            self.current_log.finalize(pr_url)
            self._save_log()
            self._save_md_report()
            print(self.current_log.summary)
    
    def _save_log(self):
        """Save log to JSON file"""
        if self.current_log:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.current_log), f, indent=2, ensure_ascii=False)
    
    def _save_md_report(self):
        """Save a Markdown report"""
        if not self.current_log:
            return
        
        md_file = self.log_dir / f"report_{self.session_id}.md"
        
        steps_md = "\n".join([
            f"| {s.step_name} | {s.status} | {s.duration_seconds:.1f}s | {s.error or '-'} |"
            for s in self.current_log.steps
        ])
        
        content = f"""# AI Coding Demo Report

## Session Info
- **Session ID**: {self.current_log.session_id}
- **Start Time**: {self.current_log.start_time}
- **Total Duration**: {self.current_log.total_duration:.1f} seconds

## Issue Information
- **Title**: {self.current_log.issue_title}
- **URL**: {self.current_log.issue_url}

## Repository
- **URL**: {self.current_log.repo_url}
- **Branch**: {self.current_log.branch_name}

## Execution Steps

| Step | Status | Duration | Error |
|------|--------|----------|-------|
{steps_md}

## Pull Request
- **URL**: {self.current_log.pr_url or 'Not created'}

## Details

{self._generate_details_md()}

---
*Generated by AI Coding Demo Assistant*
"""
        
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(content)
    
    def _generate_details_md(self) -> str:
        """Generate detailed markdown for each step"""
        if not self.current_log:
            return ""
        
        details = []
        for step in self.current_log.steps:
            step_md = f"### {step.step_name}\n\n"
            step_md += f"- Status: {step.status}\n"
            step_md += f"- Duration: {step.duration_seconds:.1f}s\n"
            if step.details:
                step_md += f"- Details:\n"
                for k, v in step.details.items():
                    step_md += f"  - {k}: {v}\n"
            if step.artifacts:
                step_md += f"- Artifacts:\n"
                for a in step.artifacts:
                    step_md += f"  - `{a}`\n"
            if step.error:
                step_md += f"- Error: `{step.error}`\n"
            details.append(step_md)
        
        return "\n".join(details)
    
    def generate_pr_description(self, log: ExecutionLog) -> str:
        """Generate PR description"""
        return f"""## Summary

🤖 This PR was created with AI Coding Demo Assistant

Implemented issue: **{log.issue_title}**

## Changes

- [ ] Implement feature/fix bug as described in #{log.issue_url.split('/')[-1]}
- [ ] Add/update tests
- [ ] Update documentation if needed

## Testing

- [ ] Run existing test suite
- [ ] Add new tests for the changes

## Additional Notes

Generated at: {datetime.now().isoformat()}
Session ID: {log.session_id}
"""
    
    def list_sessions(self) -> List[str]:
        """List all session logs"""
        return [f.stem for f in self.log_dir.glob("session_*.json")]
    
    def load_session(self, session_id: str) -> Optional[ExecutionLog]:
        """Load a specific session log"""
        session_file = self.log_dir / f"session_{session_id}.json"
        if session_file.exists():
            with open(session_file, encoding="utf-8") as f:
                data = json.load(f)
                return ExecutionLog(**data)
        return None
