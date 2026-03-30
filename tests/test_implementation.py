"""Unit tests for implementation agent"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from dataclasses import dataclass

from ai_coding_demo.agents.implementation import (
    ImplementationAgent, ImplementationPlan, ImplementationResult
)


class MockCodeFile:
    def __init__(self, path, language="Python", lines=100):
        self.path = path
        self.language = language
        self.lines = lines
        self.functions = []
        self.classes = []
        self.imports = []


class MockAnalysis:
    def __init__(self, files=None, config_files=None):
        self.files = files or []
        self.config_files = config_files or []
        self.language = "Python"
        self.local_path = Path("/tmp/test")
    
    def get_test_command(self):
        return "pytest"


class TestImplementationAgent:
    """Tests for ImplementationAgent"""
    
    def test_agent_init(self):
        agent = ImplementationAgent(Path("/tmp/test"), MockAnalysis())
        assert agent.repo_path == Path("/tmp/test")
    
    def test_extract_keywords(self):
        analysis = MockAnalysis()
        agent = ImplementationAgent(Path("/tmp/test"), analysis)
        
        keywords = agent._extract_keywords("This is a bug fix for the login function")
        
        assert "login" in keywords
        assert "function" in keywords
        assert "this" not in keywords
    
    def test_determine_approach_bug_fix(self):
        agent = ImplementationAgent(Path("/tmp/test"), MockAnalysis())
        
        approach = agent._determine_approach("Fix the bug in login", [])
        assert approach == "bug_fix"
    
    def test_determine_approach_feature(self):
        agent = ImplementationAgent(Path("/tmp/test"), MockAnalysis())
        
        approach = agent._determine_approach("Add new feature for user", [])
        assert approach == "feature_add"
    
    def test_determine_approach_test(self):
        agent = ImplementationAgent(Path("/tmp/test"), MockAnalysis())
        
        approach = agent._determine_approach("Add tests for coverage", [])
        assert approach == "test_addition"
    
    def test_estimate_complexity_low(self):
        files = [MockCodeFile("a.py", lines=50)]
        analysis = MockAnalysis(files=files)
        agent = ImplementationAgent(Path("/tmp/test"), analysis)
        
        complexity = agent._estimate_complexity("short issue", ["a.py"])
        assert complexity == "low"
    
    def test_estimate_complexity_high(self):
        files = [MockCodeFile("a.py", lines=600)]
        analysis = MockAnalysis(files=files)
        agent = ImplementationAgent(Path("/tmp/test"), analysis)
        
        complexity = agent._estimate_complexity("a" * 3000, ["a.py"])
        assert complexity == "high"
    
    def test_create_implementation_plan(self):
        files = [MockCodeFile("auth.py"), MockCodeFile("user.py")]
        analysis = MockAnalysis(files=files)
        agent = ImplementationAgent(Path("/tmp/test"), analysis)
        
        plan = agent.create_implementation_plan("Fix login bug", "Fix login")
        
        assert plan.issue_description == "Fix login bug"
        assert plan.approach == "bug_fix"
        assert len(plan.steps) > 0
    
    def test_add_simple_test(self, tmp_path):
        test_file = tmp_path / "test_example.py"
        test_file.write_text("def existing():\n    pass\n")
        
        agent = ImplementationAgent(tmp_path, MockAnalysis())
        result = agent._add_simple_test(test_file, test_file.read_text())
        
        assert result is True
        content = test_file.read_text()
        assert "test_ai_demo_addition" in content
    
    def test_add_simple_test_already_exists(self, tmp_path):
        test_file = tmp_path / "test_example.py"
        test_file.write_text("# AI Coding Demo - Test Case Added\n")
        
        agent = ImplementationAgent(tmp_path, MockAnalysis())
        result = agent._add_simple_test(test_file, test_file.read_text())
        
        assert result is False
    
    def test_add_feature_implementation_python(self, tmp_path):
        test_file = tmp_path / "example.py"
        test_file.write_text("def main():\n    pass\n")
        
        agent = ImplementationAgent(tmp_path, MockAnalysis())
        plan = ImplementationPlan(
            issue_description="Add new feature",
            related_files=[],
            approach="feature_add",
            steps=[],
            estimated_complexity="low"
        )
        
        result = agent._add_feature_implementation(test_file, test_file.read_text(), plan)
        
        assert result is True
        content = test_file.read_text()
        assert "ai_demo_feature" in content


class TestImplementationPlan:
    """Tests for ImplementationPlan dataclass"""
    
    def test_plan_creation(self):
        plan = ImplementationPlan(
            issue_description="Test",
            related_files=["a.py"],
            approach="bug_fix",
            steps=["1. Fix bug"],
            estimated_complexity="low"
        )
        
        assert plan.issue_description == "Test"
        assert plan.related_files == ["a.py"]
        assert plan.llm_used is False


class TestImplementationResult:
    """Tests for ImplementationResult dataclass"""
    
    def test_result_creation(self):
        result = ImplementationResult(
            success=True,
            files_modified=["a.py"],
            test_results="passed",
            summary="Done"
        )
        
        assert result.success is True
        assert result.files_modified == ["a.py"]
        assert result.test_results == "passed"
        assert result.llm_generated is False
