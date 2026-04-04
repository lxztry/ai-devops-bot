"""
AI DevOps Bot - Reporter
Generates various DevOps reports
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class ReportGenerator:
    """Generate DevOps reports"""
    
    TEMPLATES = {
        "daily": {
            "title": "📊 Daily Standup Report",
            "sections": ["today_completed", "in_progress", "blockers", "tomorrow"]
        },
        "weekly": {
            "title": "📈 Weekly Project Summary",
            "sections": ["highlights", "metrics", "issues_closed", "prs_merged", "next_week"]
        },
        "incident": {
            "title": "🚨 Incident Report",
            "sections": ["summary", "timeline", "impact", "resolution", "action_items"]
        }
    }
    
    def generate(self, report_type: str, data: Dict) -> str:
        """Generate a report based on type and data"""
        template = self.TEMPLATES.get(report_type, self.TEMPLATES["daily"])
        
        report = f"# {template['title']}\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        if report_type == "daily":
            report += self._generate_daily_report(data)
        elif report_type == "weekly":
            report += self._generate_weekly_report(data)
        elif report_type == "incident":
            report += self._generate_incident_report(data)
        
        return report
    
    def _generate_daily_report(self, data: Dict) -> str:
        sections = []
        
        sections.append("## ✅ Yesterday\n")
        for item in data.get("completed", []):
            sections.append(f"- {item}")
        
        sections.append("\n## 🔄 In Progress\n")
        for item in data.get("in_progress", []):
            sections.append(f"- {item}")
        
        sections.append("\n## 🚧 Blockers\n")
        blockers = data.get("blockers", [])
        if blockers:
            for item in blockers:
                sections.append(f"- {item}")
        else:
            sections.append("- None")
        
        sections.append("\n## 📅 Today\n")
        for item in data.get("planned", []):
            sections.append(f"- {item}")
        
        return "".join(sections)
    
    def _generate_weekly_report(self, data: Dict) -> str:
        sections = []
        
        sections.append("## 🎯 Highlights\n")
        for highlight in data.get("highlights", []):
            sections.append(f"- {highlight}")
        
        sections.append("\n## 📊 Metrics\n")
        metrics = data.get("metrics", {})
        sections.append(f"- Issues Closed: {metrics.get('issues_closed', 0)}\n")
        sections.append(f"- PRs Merged: {metrics.get('prs_merged', 0)}\n")
        sections.append(f"- Commits: {metrics.get('commits', 0)}\n")
        sections.append(f"- Active Contributors: {metrics.get('contributors', 0)}\n")
        
        sections.append("\n## ✅ Issues & PRs\n")
        sections.append(f"- Total Open: {metrics.get('open_issues', 0)}\n")
        sections.append(f"- Total Closed: {metrics.get('closed_issues', 0)}\n")
        
        sections.append("\n## 🔮 Next Week\n")
        for item in data.get("next_week", []):
            sections.append(f"- {item}")
        
        return "".join(sections)
    
    def _generate_incident_report(self, data: Dict) -> str:
        sections = []
        
        sections.append("## 📋 Summary\n")
        sections.append(f"{data.get('summary', 'N/A')}\n\n")
        
        sections.append("## ⏱️ Timeline\n")
        for event in data.get("timeline", []):
            sections.append(f"- [{event.get('time', '')}] {event.get('action', '')}\n")
        
        sections.append("\n## 💥 Impact\n")
        impact = data.get("impact", {})
        sections.append(f"- Duration: {impact.get('duration', 'N/A')}\n")
        sections.append(f"- Users Affected: {impact.get('users_affected', 'N/A')}\n")
        sections.append(f"- Services Impacted: {impact.get('services', 'N/A')}\n")
        
        sections.append("\n## 🛠️ Resolution\n")
        sections.append(f"{data.get('resolution', 'N/A')}\n\n")
        
        sections.append("## 📝 Action Items\n")
        for item in data.get("action_items", []):
            sections.append(f"- [ ] {item}\n")
        
        return "".join(sections)


def generate_report(report_type: str, data: Dict) -> str:
    """Convenience function for report generation"""
    generator = ReportGenerator()
    return generator.generate(report_type, data)
