#!/usr/bin/env python3
"""AI Coding Demo Assistant - Main Entry Point"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai_coding_demo.config.settings import Config, setup_interactive, print_config_status, check_config
from ai_coding_demo.core.orchestrator import MasterOrchestrator


def main():
    parser = argparse.ArgumentParser(
        description="AI Coding Demo Assistant - 全流程AI辅助GitHub Issue开发演示"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["interactive", "demo"],
        default="interactive",
        help="运行模式: interactive(交互模式) 或 demo(快速演示)"
    )
    parser.add_argument(
        "--config", "-c",
        action="store_true",
        help="进入配置向导"
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="显示当前配置状态"
    )
    parser.add_argument(
        "--workspace", "-w",
        type=Path,
        help="指定工作目录"
    )
    parser.add_argument(
        "--token", "-t",
        type=str,
        help="GitHub Personal Access Token (或设置 GITHUB_TOKEN 环境变量)"
    )
    parser.add_argument(
        "--local-demo",
        action="store_true",
        help="本地演示模式，不需要 GitHub Token"
    )
    
    args = parser.parse_args()
    
    config = Config.load()
    
    if args.token:
        config.git.token = args.token
        config.save()
        print(f"Token saved to config")
    
    if args.config:
        setup_interactive()
        return
    
    if args.status:
        print_config_status(config)
        return
    
    if args.workspace:
        config.paths.workspace = args.workspace
        config.save()
        print(f"Workspace set to: {args.workspace}")
    
    if args.local_demo:
        print("Running local demo mode (no GitHub required)")
        run_local_demo(config)
        return
    
    is_valid, missing = check_config(config)
    if not is_valid:
        print(f"Configuration incomplete. Missing: {', '.join(missing)}")
        print("Please run: python main.py --config")
        print()
        response = input("Configure now? (y/n): ").strip().lower()
        if response == 'y':
            setup_interactive()
            config = Config.load()
        else:
            return
    
    orchestrator = MasterOrchestrator(config)
    
    if args.mode == "demo":
        orchestrator.run_demo_mode()
    else:
        orchestrator.run(interactive=True)


def run_local_demo(config: Config):
    """Run a local demo without GitHub API calls"""
    print("=" * 60)
    print("   Local Demo Mode")
    print("=" * 60)
    print()
    
    from ai_coding_demo.agents.code_explorer import CodeExplorerAgent
    from ai_coding_demo.agents.dev_env import DevEnvAgent
    
    demo_repo = "https://github.com/ansible/ansible.git"
    
    print(f"1. Cloning demo repository: {demo_repo}")
    explorer = CodeExplorerAgent(config.ensure_workspace())
    
    try:
        analysis = explorer.clone_and_analyze(demo_repo, branch="devel")
        print(f"\n{analysis.structure_summary}")
        print(f"\nRuntime detected: {analysis.get_runtime()}")
        print(f"Test command: {analysis.get_test_command()}")
        
        print("\n2. Environment setup check...")
        dev_env = DevEnvAgent(analysis.local_path)
        runtime = dev_env.detect_runtime()
        print(f"   Detected runtime: {runtime or 'Unknown'}")
        
        print("\n3. Local demo complete!")
        print(f"   Repository cloned to: {analysis.local_path}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
