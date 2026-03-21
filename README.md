# AI Coding Demo Assistant

An AI-powered assistant that demonstrates end-to-end AI coding capabilities by automatically discovering GitHub issues, analyzing code, implementing changes, and creating pull requests.

## Quick Start

### 1. Configure the Assistant

```bash
cd ai_coding_demo
python -m ai_coding_demo.config.settings
```

Required settings:
- Git username and email
- GitHub Personal Access Token

### 2. Run the Demo

```bash
# Interactive mode (recommended)
python main.py

# Demo mode (minimal interaction)
python main.py --mode demo
```

## Features

- **GitHub Issue Discovery** - Search and filter issues based on your preferences
- **Code Analysis** - Understand repository structure and dependencies
- **Environment Setup** - Auto-detect and install dependencies
- **Smart Implementation** - Generate code changes based on issue requirements
- **Git Operations** - Handle branches, commits, and PRs automatically
- **Execution Logging** - Track and document the entire process

## Project Structure

```
ai_coding_demo/
├── agents/              # Individual agent implementations
│   ├── repo_scout.py    # GitHub issue discovery
│   ├── code_explorer.py # Code analysis
│   ├── dev_env.py       # Environment setup
│   ├── git_ops.py       # Git operations
│   ├── docs_logger.py   # Documentation & logging
│   └── implementation.py # Code implementation
├── config/              # Configuration management
│   └── settings.py      # Config classes and setup
├── core/                # Core orchestration
│   └── orchestrator.py  # Master workflow coordinator
├── logs/                # Execution logs
└── main.py             # Entry point
```

## Supported Languages

- Python
- JavaScript/TypeScript
- Go
- Rust
- And more...

## How It Works

```
┌──────────────────────────────────────────────────────┐
│              Master Orchestrator                     │
│         (Coordinates all agents)                     │
└─────────────────────┬────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┬──────────────┐
    │                 │                 │              │
    ▼                 ▼                 ▼              ▼
┌─────────┐    ┌───────────┐    ┌───────────┐   ┌─────────────┐
│  Repo   │    │   Code    │    │   Dev     │   │    Git      │
│ Scout   │───▶│ Explorer  │───▶│ Env       │──▶│ Ops         │
│         │    │           │    │ Agent     │   │             │
└─────────┘    └───────────┘    └───────────┘   └─────────────┘
      │                                    │              │
      │                                    ▼              │
      │                              ┌───────────┐       │
      │                              │Implementation│    │
      │                              │   Agent    │──────┘
      │                              └───────────┘
      └────────────────────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │  Docs Logger  │
              │(Documentation)│
              └───────────────┘
```

## Requirements

- Python 3.8+
- Git
- GitHub Personal Access Token
- GitHub CLI (optional, for better PR creation)

## License

MIT
