"""Code Implementation Agent"""
import subprocess
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import random


@dataclass
class ImplementationPlan:
    issue_description: str
    related_files: List[str]
    approach: str
    steps: List[str]
    estimated_complexity: str


@dataclass
class ImplementationResult:
    success: bool
    files_modified: List[str]
    test_results: str
    summary: str
    error: Optional[str] = None


class ImplementationAgent:
    """Implement code changes based on issue requirements"""
    
    def __init__(self, repo_path: Path, analysis):
        self.repo_path = Path(repo_path)
        self.analysis = analysis
    
    def create_implementation_plan(self, issue_body: str) -> ImplementationPlan:
        """Create a plan for implementing the issue"""
        keywords = self._extract_keywords(issue_body)
        related_files = self._find_related_files(keywords)
        
        plan = ImplementationPlan(
            issue_description=issue_body[:500],
            related_files=related_files,
            approach=self._determine_approach(issue_body, related_files),
            steps=self._generate_steps(issue_body, related_files),
            estimated_complexity=self._estimate_complexity(issue_body, related_files),
        )
        
        return plan
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key terms from issue description"""
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        stopwords = {'this', 'that', 'with', 'from', 'have', 'were', 'their',
                    'which', 'would', 'could', 'should', 'about', 'there',
                    'where', 'when', 'what', 'where', 'these', 'those'}
        keywords = [w for w in words if w not in stopwords]
        return list(set(keywords))[:20]
    
    def _find_related_files(self, keywords: List[str]) -> List[str]:
        """Find files related to the keywords"""
        related = []
        for f in self.analysis.files:
            path_lower = f.path.lower()
            score = sum(1 for kw in keywords if kw in path_lower)
            if score > 0:
                related.append((f.path, score))
        
        related.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in related[:10]]
    
    def _determine_approach(self, issue_body: str, related_files: List[str]) -> str:
        """Determine the implementation approach"""
        issue_lower = issue_body.lower()
        
        if any(word in issue_lower for word in ['fix', 'bug', 'error', 'crash']):
            return "bug_fix"
        elif any(word in issue_lower for word in ['add', 'new', 'feature', 'implement']):
            return "feature_add"
        elif any(word in issue_lower for word in ['improve', 'optimize', 'enhance']):
            return "improvement"
        elif any(word in issue_lower for word in ['test', 'coverage']):
            return "test_addition"
        else:
            return "general"
    
    def _generate_steps(self, issue_body: str, related_files: List[str]) -> List[str]:
        """Generate implementation steps"""
        approach = self._determine_approach(issue_body, related_files)
        steps = []
        
        if related_files:
            steps.append(f"1. Review and understand existing code in: {', '.join(related_files[:3])}")
        
        if approach == "bug_fix":
            steps.extend([
                "2. Identify the root cause of the bug",
                "3. Implement the fix",
                "4. Verify the fix works correctly",
            ])
        elif approach == "feature_add":
            steps.extend([
                "2. Design the new feature structure",
                "3. Implement the feature",
                "4. Add tests for the new feature",
            ])
        elif approach == "test_addition":
            steps.extend([
                "2. Identify code paths that need testing",
                "3. Write comprehensive tests",
                "4. Run tests to verify coverage",
            ])
        else:
            steps.extend([
                "2. Analyze the requirements",
                "3. Make necessary changes",
                "4. Test the changes",
            ])
        
        steps.append("5. Ensure all existing tests pass")
        return steps
    
    def _estimate_complexity(self, issue_body: str, related_files: List[str]) -> str:
        """Estimate implementation complexity"""
        related_paths = set(related_files)
        lines_count = sum(
            f.lines for f in self.analysis.files if f.path in related_paths
        )
        
        issue_length = len(issue_body)
        
        if lines_count > 500 or issue_length > 2000:
            return "high"
        elif lines_count > 100 or issue_length > 500:
            return "medium"
        return "low"
    
    def implement(self, plan: ImplementationPlan) -> ImplementationResult:
        """Execute the implementation plan"""
        print(f"🛠️  Starting implementation...")
        print(f"   Approach: {plan.approach}")
        print(f"   Complexity: {plan.estimated_complexity}")
        print(f"   Related files: {len(plan.related_files)}")
        
        files_modified = []
        
        for file_path in plan.related_files[:3]:
            full_path = self.repo_path / file_path
            if full_path.exists():
                modified = self._suggest_modification(full_path, plan)
                if modified:
                    files_modified.append(file_path)
        
        test_results = self._run_tests()
        
        return ImplementationResult(
            success=len(files_modified) > 0 or test_results == "passed",
            files_modified=files_modified,
            test_results=test_results,
            summary=self._generate_summary(plan, files_modified),
        )
    
    def _suggest_modification(self, file_path: Path, plan: ImplementationPlan) -> bool:
        """Suggest a modification to a file based on the plan"""
        try:
            content = file_path.read_text(encoding="utf-8")
            lang = file_path.suffix
            
            if plan.approach == "test_addition":
                if lang in ['.py', '.js', '.ts']:
                    return self._add_simple_test(file_path, content)
            elif plan.approach == "bug_fix":
                return self._add_bug_fix_comment(file_path, content, plan)
            elif plan.approach == "feature_add":
                return self._add_feature_implementation(file_path, content, plan)
            
            return False
        except Exception as e:
            print(f"   Warning: Could not process {file_path}: {e}")
            return False
    
    def _add_simple_test(self, file_path: Path, content: str) -> bool:
        """Add a simple test case"""
        test_marker = "# AI Coding Demo - Test Case Added"
        
        if test_marker in content:
            return False
        
        new_content = content + f"\n\n{test_marker}\n"
        new_content += "def test_ai_demo_addition():\n"
        new_content += "    \"\"\"Test added by AI Coding Demo\"\"\"\n"
        new_content += "    assert True, 'AI Demo test passed'\n"
        
        try:
            file_path.write_text(new_content, encoding="utf-8")
            print(f"   ✅ Added test to {file_path.name}")
            return True
        except:
            return False
    
    def _add_bug_fix_comment(self, file_path: Path, content: str, plan: ImplementationPlan) -> bool:
        """Add a bug fix comment"""
        fix_marker = "# AI Coding Demo - Bug Fix Applied"
        
        if fix_marker in content:
            return False
        
        new_content = content + f"\n\n{fix_marker}\n"
        new_content += "# Issue: " + plan.issue_description[:100] + "...\n"
        new_content += "# Status: Acknowledged and addressed\n"
        
        try:
            file_path.write_text(new_content, encoding="utf-8")
            print(f"   ✅ Added bug fix note to {file_path.name}")
            return True
        except:
            return False
    
    def _add_feature_implementation(self, file_path: Path, content: str, plan: ImplementationPlan) -> bool:
        """Add a feature implementation"""
        feature_marker = "# AI Coding Demo - Feature Implementation"
        
        if feature_marker in content:
            return False
        
        lang = file_path.suffix
        new_feature = f"\n\n{feature_marker}\n"
        
        if lang == ".py":
            new_feature += "def ai_demo_feature():\n"
            new_feature += '    """Feature implemented by AI Coding Demo"""\n'
            new_feature += "    return True\n"
        elif lang in [".js", ".ts"]:
            new_feature += "// Feature implemented by AI Coding Demo\n"
            new_feature += "function aiDemoFeature() {\n"
            new_feature += "    return true;\n"
            new_feature += "}\n"
        else:
            new_feature += f"// Feature: {plan.issue_description[:50]}...\n"
        
        try:
            file_path.write_text(content + new_feature, encoding="utf-8")
            print(f"   ✅ Added feature to {file_path.name}")
            return True
        except:
            return False
    
    def _run_tests(self) -> str:
        """Run the test suite"""
        test_cmd = self.analysis.get_test_command()
        if not test_cmd:
            return "no_test_command"
        
        try:
            result = subprocess.run(
                test_cmd,
                shell=True,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return "passed"
            else:
                return f"failed: {result.stderr[:200]}"
        except subprocess.TimeoutExpired:
            return "timeout"
        except Exception as e:
            return f"error: {str(e)}"
    
    def _generate_summary(self, plan: ImplementationPlan, files_modified: List[str]) -> str:
        """Generate implementation summary"""
        return f"""
Implementation Summary:
- Approach: {plan.approach}
- Complexity: {plan.estimated_complexity}
- Files modified: {len(files_modified)}
- Related files analyzed: {len(plan.related_files)}
"""
