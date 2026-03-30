"""Code Exploration Agent with AST analysis"""
import ast
import json
import subprocess
import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Any
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

from ai_coding_demo.core.utils import safe_execute


logger = logging.getLogger(__name__)


@dataclass
class CodeFile:
    path: str
    language: str
    lines: int
    purpose: str = ""
    dependencies: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)


@dataclass 
class DependencyGraph:
    nodes: Dict[str, Set[str]] = field(default_factory=dict)
    reverse: Dict[str, Set[str]] = field(default_factory=dict)
    
    def add_edge(self, from_module: str, to_module: str):
        if from_module not in self.nodes:
            self.nodes[from_module] = set()
        self.nodes[from_module].add(to_module)
        
        if to_module not in self.reverse:
            self.reverse[to_module] = set()
        self.reverse[to_module].add(from_module)
    
    def get_dependents(self, module: str) -> Set[str]:
        return self.reverse.get(module, set())
    
    def get_dependencies(self, module: str) -> Set[str]:
        return self.nodes.get(module, set())


@dataclass
class RepoAnalysis:
    repo_url: str
    local_path: Path
    language: str
    files: List[CodeFile] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    main_files: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    structure_summary: str = ""
    key_modules: List[str] = field(default_factory=list)
    dependency_graph: DependencyGraph = field(default_factory=DependencyGraph)
    ast_analysis: Dict[str, dict] = field(default_factory=dict)
    
    def get_test_command(self) -> Optional[str]:
        """Get the command to run tests"""
        if self.config_files:
            for f in self.config_files:
                if "package.json" in f:
                    return "npm test"
                elif "pytest.ini" in f or "pyproject.toml" in f:
                    return "pytest"
                elif "Cargo.toml" in f:
                    return "cargo test"
                elif "go.mod" in f:
                    return "go test ./..."
        return None
    
    def get_install_command(self) -> Optional[str]:
        """Get the command to install dependencies"""
        if self.config_files:
            for f in self.config_files:
                if "package.json" in f:
                    return "npm install"
                elif "requirements.txt" in f:
                    return "pip install -r requirements.txt"
                elif "pyproject.toml" in f:
                    return "pip install -e ."
                elif "Cargo.toml" in f:
                    return "cargo build"
                elif "go.mod" in f:
                    return "go mod download"
        return None
    
    def get_runtime(self) -> Optional[str]:
        """Detect the programming runtime"""
        lang_map = {
            "package.json": "Node.js",
            "requirements.txt": "Python",
            "pyproject.toml": "Python",
            "Cargo.toml": "Rust",
            "go.mod": "Go",
            "pom.xml": "Java",
            "build.gradle": "Java/Kotlin",
            "composer.json": "PHP",
        }
        for f in self.config_files:
            for key, runtime in lang_map.items():
                if key in f:
                    return runtime
        return self.language or "Unknown"


class CodeExplorerAgent:
    """Explore and understand codebase structure"""
    
    LANGUAGE_EXTENSIONS = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "JavaScript",
        ".tsx": "TypeScript",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".kt": "Kotlin",
        ".php": "PHP",
        ".rb": "Ruby",
        ".cs": "C#",
        ".cpp": "C++",
        ".c": "C",
    }
    
    TEST_PATTERNS = [
        "test_", "_test.py", "tests/", "__tests__/",
        ".test.", ".spec.", "/test/", "/tests/",
        "*_test.go", "_test.go",
    ]
    
    CONFIG_PATTERNS = [
        "package.json", "requirements.txt", "pyproject.toml",
        "Cargo.toml", "go.mod", "go.sum", "pom.xml", "build.gradle",
        "composer.json", "Gemfile", "Makefile", "Dockerfile",
        ".eslintrc", ".prettierrc", "tsconfig.json", "jest.config",
        "pytest.ini", "setup.py", "setup.cfg",
    ]
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
    
    def clone_and_analyze(self, repo_url: str, branch: str = "main") -> RepoAnalysis:
        """Clone repository and analyze its structure"""
        repo_name = self._extract_repo_name(repo_url)
        local_path = self.workspace / repo_name
        
        if not local_path.exists():
            print(f"📥 Cloning repository to {local_path}...")
            self._clone_repo(repo_url, local_path, branch)
        else:
            print(f"📂 Repository already exists at {local_path}")
        
        return self.analyze(local_path, repo_url)
    
    def _clone_repo(self, url: str, path: Path, branch: str = "main"):
        """Clone a git repository"""
        try:
            subprocess.run(
                ["git", "clone", "--branch", branch, "--depth", "1", url, str(path)],
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Clone failed: {e.stderr.decode() if e.stderr else str(e)}")
            raise
    
    def _extract_repo_name(self, url: str) -> str:
        """Extract repository name from URL"""
        if "/" in url:
            parts = url.rstrip("/").split("/")
            name = parts[-1]
            if name.endswith(".git"):
                name = name[:-4]
            return name
        return url
    
    def analyze(self, local_path: Path, repo_url: str) -> RepoAnalysis:
        """Analyze repository structure"""
        print(f"🔍 Analyzing repository at {local_path}...")
        
        git_dir = local_path / ".git"
        files = [f for f in local_path.rglob("*") 
                 if f.is_file() and not f.is_relative_to(git_dir)]
        file_paths = files
        
        code_files = []
        test_files = []
        config_files = []
        main_files = []
        
        for f in file_paths:
            rel_path = str(f.relative_to(local_path))
            ext = f.suffix.lower()
            lang = self.LANGUAGE_EXTENSIONS.get(ext, "Other")
            
            is_test = any(pattern in rel_path for pattern in self.TEST_PATTERNS)
            is_config = any(pattern in f.name for pattern in self.CONFIG_PATTERNS)
            
            if is_test:
                test_files.append(rel_path)
            elif is_config:
                config_files.append(rel_path)
            elif ext in self.LANGUAGE_EXTENSIONS:
                code_files.append(CodeFile(
                    path=rel_path,
                    language=lang,
                    lines=self._count_lines(f),
                ))
                if self._is_main_file(f, rel_path):
                    main_files.append(rel_path)
        
        analysis = RepoAnalysis(
            repo_url=repo_url,
            local_path=local_path,
            language=self._detect_primary_language(code_files),
            files=code_files,
            test_files=test_files,
            config_files=config_files,
            main_files=main_files,
            dependencies=self._parse_dependencies(local_path, config_files),
        )
        
        analysis.structure_summary = self._generate_summary(analysis)
        analysis.key_modules = self._find_key_modules(code_files, main_files)
        
        return analysis
    
    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file"""
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except (IOError, OSError):
            return 0
    
    def _is_main_file(self, file_path: Path, rel_path: str) -> bool:
        """Check if file is a main/entry point"""
        name = file_path.name.lower()
        return any(n in name for n in ["main", "index", "app", "server"]) or \
               rel_path.startswith("src/") and file_path.suffix in [".js", ".ts", ".py"]
    
    def _detect_primary_language(self, files: List[CodeFile]) -> str:
        """Detect primary language from files"""
        if not files:
            return "Unknown"
        lang_counts: Dict[str, int] = {}
        for f in files:
            lang_counts[f.language] = lang_counts.get(f.language, 0) + 1
        if not lang_counts:
            return "Unknown"
        primary_lang = max(lang_counts.keys(), key=lambda k: lang_counts[k])
        return primary_lang
    
    def _parse_dependencies(self, local_path: Path, config_files: List[str]) -> Dict[str, str]:
        """Parse dependencies from config files"""
        deps = {}
        
        for cf in config_files:
            if "package.json" in cf:
                deps.update(self._parse_package_json(local_path / cf))
            elif "requirements.txt" in cf:
                deps.update(self._parse_requirements_txt(local_path / cf))
        
        return deps
    
    def _parse_package_json(self, path: Path) -> Dict[str, str]:
        """Parse package.json for dependencies"""
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            all_deps = {}
            all_deps.update(data.get("dependencies", {}))
            all_deps.update(data.get("devDependencies", {}))
            return all_deps
        except (IOError, json.JSONDecodeError):
            return {}
    
    def _parse_requirements_txt(self, path: Path) -> Dict[str, str]:
        """Parse requirements.txt"""
        deps = {}
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("-"):
                        if ">=" in line:
                            pkg, ver = line.split(">=", 1)
                            deps[pkg.strip()] = f">={ver.strip()}"
                        elif "==" in line:
                            pkg, ver = line.split("==", 1)
                            deps[pkg.strip()] = f"=={ver.strip()}"
                        else:
                            deps[line] = "latest"
        except (IOError, OSError):
            pass
        return deps
    
    def _generate_summary(self, analysis: RepoAnalysis) -> str:
        """Generate a human-readable summary"""
        lines = [
            f"📊 仓库分析摘要",
            f"   语言: {analysis.language}",
            f"   代码文件: {len(analysis.files)}",
            f"   测试文件: {len(analysis.test_files)}",
            f"   配置文件: {len(analysis.config_files)}",
            f"   入口文件: {', '.join(analysis.main_files[:3])}",
        ]
        
        if analysis.dependencies:
            dep_count = len(analysis.dependencies)
            lines.append(f"   依赖数量: {dep_count}")
        
        return "\n".join(lines)
    
    def _find_key_modules(self, code_files: List[CodeFile], main_files: List[str]) -> List[str]:
        """Find key modules in the codebase"""
        modules = []
        
        for f in code_files:
            if any(m in f.path for m in main_files):
                modules.append(f.path)
            elif f.path.startswith("src/") and f.lines > 50:
                modules.append(f.path)
        
        return modules[:10]
    
    def find_related_files(self, analysis: RepoAnalysis, keywords: List[str]) -> List[str]:
        """Find files related to specific keywords"""
        related = []
        for f in analysis.files:
            path_lower = f.path.lower()
            if any(kw.lower() in path_lower for kw in keywords):
                related.append(f.path)
        return related
    
    def analyze_with_ast(self, local_path: Path, repo_url: str, parallel: bool = True) -> RepoAnalysis:
        """Analyze repository with AST parsing"""
        print(f"🔍 Analyzing repository with AST...")
        
        analysis = self.analyze(local_path, repo_url)
        
        if parallel:
            analysis = self._analyze_files_parallel(analysis)
        else:
            analysis = self._analyze_files_sequential(analysis)
        
        analysis.dependency_graph = self._build_dependency_graph(analysis)
        analysis.ast_analysis = self._generate_ast_summary(analysis)
        
        return analysis
    
    def _analyze_files_parallel(self, analysis: RepoAnalysis) -> RepoAnalysis:
        """Analyze files in parallel using ThreadPoolExecutor"""
        py_files = [f for f in analysis.files if f.language == "Python"]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(self._analyze_python_file, py_files))
        
        file_map = {f.path: f for f in analysis.files}
        for result in results:
            if result and result.path in file_map:
                code_file = file_map[result.path]
                code_file.functions = result.functions
                code_file.classes = result.classes
                code_file.imports = result.imports
        
        return analysis
    
    def _analyze_files_sequential(self, analysis: RepoAnalysis) -> RepoAnalysis:
        """Analyze files sequentially"""
        for code_file in analysis.files:
            if code_file.language == "Python":
                result = self._analyze_python_file(code_file)
                if result:
                    code_file.functions = result.functions
                    code_file.classes = result.classes
                    code_file.imports = result.imports
        return analysis
    
    @safe_execute(default=None)
    def _analyze_python_file(self, code_file: CodeFile) -> Optional[CodeFile]:
        """Analyze a Python file using AST"""
        local_path = code_file.path
        full_path = Path(local_path)
        
        if not full_path.exists():
            full_path = Path(code_file.path)
        
        try:
            with open(full_path, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(full_path))
            
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif node.module:
                        imports.append(node.module)
            
            code_file.functions = functions
            code_file.classes = classes
            code_file.imports = imports
            
            return code_file
        except Exception as e:
            logger.debug(f"AST analysis failed for {code_file.path}: {e}")
            return None
    
    def _build_dependency_graph(self, analysis: RepoAnalysis) -> DependencyGraph:
        """Build module dependency graph"""
        graph = DependencyGraph()
        
        for code_file in analysis.files:
            module_name = self._get_module_name(code_file.path)
            
            for imp in code_file.imports:
                graph.add_edge(module_name, imp)
        
        return graph
    
    def _get_module_name(self, file_path: str) -> str:
        """Convert file path to module name"""
        path = Path(file_path)
        if path.suffix == ".py":
            return str(path.with_suffix("")).replace("/", ".")
        return file_path
    
    def _generate_ast_summary(self, analysis: RepoAnalysis) -> Dict[str, Any]:
        """Generate AST analysis summary"""
        total_functions = sum(len(f.functions) for f in analysis.files)
        total_classes = sum(len(f.classes) for f in analysis.files)
        
        file_counts: Dict[str, int] = {}
        for code_file in analysis.files:
            file_counts[code_file.language] = file_counts.get(code_file.language, 0) + 1
        
        return {
            "total_functions": total_functions,
            "total_classes": total_classes,
            "files_by_language": file_counts,
            "avg_functions_per_file": total_functions / len(analysis.files) if analysis.files else 0,
        }
    
    def find_affected_files(self, analysis: RepoAnalysis, target_file: str) -> List[str]:
        """Find files that might be affected by changes to target file"""
        graph = analysis.dependency_graph
        module_name = self._get_module_name(target_file)
        
        affected = set()
        
        affected.update(graph.get_dependents(module_name))
        
        for code_file in analysis.files:
            if any(target_file.split("/")[-1] in imp for imp in code_file.imports):
                affected.add(self._get_module_name(code_file.path))
        
        return list(affected)
