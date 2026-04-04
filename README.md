# AI DevOps Bot 🤖

AI-powered DevOps automation bot that helps streamline CI/CD workflows, auto-classify issues, and provide smart code review suggestions.

## Features

### 🚀 CI/CD Automation
- **Auto Build Trigger**: Automatically trigger builds based on code changes
- **Smart Deploy**: AI-optimized deployment strategies
- **Rollback Helper**: Intelligent rollback recommendations

### 🔍 Issue Intelligence
- **Auto Classification**: Automatically categorize issues (bug, feature, docs, etc.)
- **Priority Assessment**: AI evaluates issue priority based on content
- **Duplicate Detection**: Find similar existing issues

### 📝 Code Review Assistant
- **PR Analysis**: Review pull requests with AI insights
- **Code Suggestions**: Recommend improvements
- **Security Scan**: Basic security vulnerability detection

### 📊 Reporting
- **Daily Standup**: Auto-generate standup reports
- **Weekly Summary**: Project health summaries
- **Custom Reports**: Flexible reporting templates

## Quick Start

### Prerequisites
- Python 3.9+
- GitHub Token
- OpenAI API Key (optional for AI features)

### Installation

```bash
git clone https://github.com/lxztry/ai-devops-bot.git
cd ai-devops-bot
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Edit .env with your tokens
```

```env
GITHUB_TOKEN=your_github_token
OPENAI_API_KEY=your_openai_key  # Optional
WEBHOOK_SECRET=your_webhook_secret
```

### Run

```bash
python main.py
```

## GitHub Actions Integration

Add to your workflow:

```yaml
name: AI DevOps Bot
on: [issues, pull_request]

jobs:
  ai-bot:
    runs-on: ubuntu-latest
    steps:
      - uses: lxztry/ai-devops-bot@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          openai-key: ${{ secrets.OPENAI_API_KEY }}
```

## Usage Examples

### Issue Classification

```bash
# Classify an issue
python -m cli classify --issue 123

# Output:
# Title: "Login button not working"
# Classification: 🐛 Bug (confidence: 92%)
# Priority: High
# Suggested Labels: bug, priority-high, frontend
```

### Auto PR Review

```bash
# Review a PR
python -m cli review --pr 456

# Output:
# 📝 PR Review for #456
# ✅ Code Quality: Good
# ⚠️ Suggestions: 2
# 🔒 Security: Pass
# 💡 Recommendations provided
```

### Generate Report

```bash
# Generate weekly report
python -m cli report --type weekly --repo owner/repo

# Output saved to: reports/weekly_2026-04-04.md
```

## Architecture

```
ai-devops-bot/
├── bot/                    # Main bot logic
│   ├── __init__.py
│   ├── classifier.py       # Issue classification
│   ├── reviewer.py         # PR review
│   ├── reporter.py         # Report generation
│   └── deployer.py        # Deploy automation
├── cli/                   # CLI interface
├── api/                   # API endpoints
├── utils/                 # Utilities
├── templates/             # Report templates
└── main.py               # Entry point
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | Required |
| `OPENAI_API_KEY` | OpenAI API Key for AI features | Optional |
| `DEFAULT_LABELS` | Default labels for classification | ["bug", "feature"] |
| `AUTO_ASSIGN` | Auto-assign issues | true |

## License

MIT
