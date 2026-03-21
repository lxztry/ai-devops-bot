"""Development Environment Setup Agent"""
import subprocess
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict
import shutil


@dataclass
class EnvSetupResult:
    success: bool
    runtime: str
    installed_deps: List[str] = field(default_factory=list)
    test_result: Optional[str] = None
    error: Optional[str] = None


class DevEnvAgent:
    """Setup and manage development environment"""
    
    RUNTIME_CHECKS = {
        "Python": ["python", "--version"],
        "Node.js": ["node", "--version"],
        "Go": ["go", "version"],
        "Rust": ["cargo", "--version"],
        "Java": ["java", "-version"],
    }
    
    INSTALL_COMMANDS = {
        "Python": {
            "package.json": "pip install -r requirements.txt",
            "pyproject.toml": "pip install -e .",
            "setup.py": "pip install -e .",
        },
        "Node.js": {
            "package.json": "npm install",
        },
        "Go": {
            "go.mod": "go mod download",
        },
        "Rust": {
            "Cargo.toml": "cargo build",
        },
    }
    
    TEST_COMMANDS = {
        "Python": "python -m pytest -v",
        "Node.js": "npm test",
        "Go": "go test ./...",
        "Rust": "cargo test",
        "Java": "mvn test",
    }
    
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
    
    def detect_runtime(self) -> Optional[str]:
        """Detect the programming runtime"""
        for runtime, check_cmd in self.RUNTIME_CHECKS.items():
            try:
                result = subprocess.run(
                    check_cmd,
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return runtime
            except:
                continue
        return None
    
    def find_dependency_files(self) -> List[str]:
        """Find dependency configuration files"""
        dep_files = []
        for pattern in ["package.json", "requirements.txt", "pyproject.toml", 
                       "Cargo.toml", "go.mod", "pom.xml", "build.gradle"]:
            matches = list(self.repo_path.rglob(pattern))
            dep_files.extend([str(m) for m in matches])
        return dep_files
    
    def install_dependencies(self, runtime: str, dep_files: List[str]) -> EnvSetupResult:
        """Install project dependencies"""
        if not dep_files:
            return EnvSetupResult(success=True, runtime=runtime)
        
        installed = []
        errors = []
        
        for dep_file in dep_files:
            dep_name = Path(dep_file).name
            install_cmd = None
            
            for runtime_key, commands in self.INSTALL_COMMANDS.items():
                if runtime_key.lower() in runtime.lower():
                    install_cmd = commands.get(dep_name)
                    break
            
            if install_cmd:
                print(f"📦 Installing dependencies from {dep_name}...")
                try:
                    result = subprocess.run(
                        install_cmd,
                        shell=True,
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    if result.returncode == 0:
                        installed.append(dep_name)
                    else:
                        errors.append(f"{dep_name}: {result.stderr[:200]}")
                except subprocess.TimeoutExpired:
                    errors.append(f"{dep_name}: Installation timeout")
                except Exception as e:
                    errors.append(f"{dep_name}: {str(e)}")
        
        return EnvSetupResult(
            success=len(errors) == 0,
            runtime=runtime,
            installed_deps=installed,
            error="\n".join(errors) if errors else None
        )
    
    def run_baseline_tests(self, runtime: str) -> EnvSetupResult:
        """Run baseline tests to verify environment"""
        test_cmd = self.TEST_COMMANDS.get(runtime)
        
        if not test_cmd:
            return EnvSetupResult(success=False, runtime=runtime, error="No test command found")
        
        print(f"🧪 Running baseline tests...")
        try:
            result = subprocess.run(
                test_cmd,
                shell=True,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return EnvSetupResult(
                success=result.returncode == 0,
                runtime=runtime,
                test_result=result.stdout + result.stderr
            )
        except subprocess.TimeoutExpired:
            return EnvSetupResult(success=False, runtime=runtime, error="Test timeout")
        except Exception as e:
            return EnvSetupResult(success=False, runtime=runtime, error=str(e))
    
    def setup(self) -> EnvSetupResult:
        """Full environment setup process"""
        print("🔧 Setting up development environment...")
        
        runtime = self.detect_runtime()
        if not runtime:
            return EnvSetupResult(
                success=False, 
                runtime="Unknown",
                error="Could not detect runtime. Please ensure Python, Node.js, Go, or Rust is installed."
            )
        
        print(f"✅ Detected runtime: {runtime}")
        
        dep_files = self.find_dependency_files()
        if dep_files:
            install_result = self.install_dependencies(runtime, dep_files)
            if not install_result.success:
                return install_result
        
        test_result = self.run_baseline_tests(runtime)
        return test_result
    
    def check_tool_available(self, tool: str) -> bool:
        """Check if a tool is available"""
        try:
            result = subprocess.run(
                ["which" if os.name != "nt" else "where", tool],
                capture_output=True
            )
            return result.returncode == 0
        except:
            return False
