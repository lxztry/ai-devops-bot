"""
AI DevOps Bot - Main Entry Point
"""

import os
import sys
from bot.classifier import classify_issue, IssueClassifier
from bot.reporter import generate_report

def main():
    """Main entry point for the bot"""
    
    print("""
    ╔═══════════════════════════════════════════╗
    ║     🤖 AI DevOps Bot                      ║
    ║     Your AI-powered DevOps assistant      ║
    ╚═══════════════════════════════════════════╝
    """)
    
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1]
    
    if command == "classify":
        handle_classify()
    elif command == "report":
        handle_report()
    elif command == "--help" or command == "-h":
        print_help()
    else:
        print(f"Unknown command: {command}")
        print_help()


def print_help():
    """Print help message"""
    print("""
Usage:
    python main.py <command> [options]

Commands:
    classify    Classify an issue
    report      Generate a report

Examples:
    # Classify an issue
    python main.py classify "Fix login bug"
    
    # Generate daily report
    python main.py report --type daily
    
    # Generate weekly report
    python main.py report --type weekly

Options:
    -h, --help    Show this help message
""")


def handle_classify():
    """Handle classify command"""
    if len(sys.argv) < 3:
        print("Usage: python main.py classify <issue_title>")
        return
    
    title = sys.argv[2]
    body = sys.argv[3] if len(sys.argv) > 3 else ""
    
    result = classify_issue(title, body)
    
    print(f"""
📋 Classification Result
━━━━━━━━━━━━━━━━━━━━━━━━━━

Category: {result['category']}
Priority: {result['priority']}
Confidence: {result['confidence']:.0%}
Labels: {', '.join(result['labels'])}

💡 Suggestions:""")
    
    for suggestion in result.get('suggestions', []):
        print(f"  • {suggestion}")


def handle_report():
    """Handle report command"""
    report_type = "daily"
    
    if len(sys.argv) > 2 and sys.argv[2] == "--type":
        if len(sys.argv) > 3:
            report_type = sys.argv[3]
    
    # Sample data for demo
    sample_data = {
        "daily": {
            "completed": ["Fixed authentication bug", "Updated docs"],
            "in_progress": ["Implementing new feature"],
            "blockers": [],
            "planned": ["Code review", "Write tests"]
        },
        "weekly": {
            "highlights": ["Launched v2.0", "Fixed 50+ bugs"],
            "metrics": {
                "issues_closed": 45,
                "prs_merged": 23,
                "commits": 156,
                "contributors": 8
            },
            "next_week": ["Performance optimization", "Security audit"]
        }
    }
    
    data = sample_data.get(report_type, sample_data["daily"])
    report = generate_report(report_type, data)
    
    print(report)


if __name__ == "__main__":
    main()
