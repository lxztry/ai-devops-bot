"""
AI DevOps Bot - Issue Classifier
"""

import re
from typing import Dict, List, Optional

class IssueClassifier:
    """Classifies GitHub issues using keyword matching and AI"""
    
    CATEGORIES = {
        "bug": {
            "keywords": ["bug", "error", "crash", "fail", "broken", "issue", "not working", "wrong"],
            "priority": "high",
            "labels": ["bug", "priority-high"]
        },
        "feature": {
            "keywords": ["feature", "request", "enhancement", "improvement", "add", "implement"],
            "priority": "medium",
            "labels": ["enhancement", "feature-request"]
        },
        "docs": {
            "keywords": ["doc", "documentation", "readme", "guide", "example"],
            "priority": "low",
            "labels": ["documentation"]
        },
        "performance": {
            "keywords": ["slow", "performance", "optimize", "speed", "memory"],
            "priority": "medium",
            "labels": ["performance", "optimization"]
        },
        "security": {
            "keywords": ["security", "vulnerability", "hack", "exploit", "injection"],
            "priority": "high",
            "labels": ["security", "priority-critical"]
        },
        "question": {
            "keywords": ["how", "what", "why", "question", "?", "help"],
            "priority": "low",
            "labels": ["question"]
        }
    }
    
    def classify(self, title: str, body: str = "") -> Dict:
        """
        Classify an issue based on title and body content
        
        Returns:
            Dict with: category, priority, labels, confidence
        """
        text = f"{title} {body}".lower()
        
        scores = {}
        for category, config in self.CATEGORIES.items():
            score = 0
            matches = 0
            for keyword in config["keywords"]:
                if keyword.lower() in text:
                    score += 1
                    matches += 1
            if matches > 0:
                confidence = min(0.95, 0.5 + (matches * 0.15))
                scores[category] = {
                    "score": score,
                    "confidence": confidence
                }
        
        if not scores:
            return {
                "category": "unknown",
                "priority": "medium",
                "labels": ["needs-triage"],
                "confidence": 0.0
            }
        
        best_category = max(scores.keys(), key=lambda k: scores[k]["score"])
        config = self.CATEGORIES[best_category]
        
        return {
            "category": best_category,
            "priority": config["priority"],
            "labels": config["labels"],
            "confidence": scores[best_category]["confidence"],
            "suggestions": self._generate_suggestions(best_category, title)
        }
    
    def _generate_suggestions(self, category: str, title: str) -> List[str]:
        """Generate helpful suggestions based on category"""
        suggestions = {
            "bug": [
                "Check if similar issues already exist",
                "Add steps to reproduce",
                "Include error messages/screenshots"
            ],
            "feature": [
                "Explain the use case",
                "Describe expected behavior",
                "Consider API design"
            ],
            "docs": [
                "Specify which documentation needs update",
                "Provide link to relevant docs"
            ],
            "performance": [
                "Include benchmarks if possible",
                "Describe expected vs actual performance"
            ],
            "security": [
                "Do NOT include sensitive data",
                "Follow responsible disclosure"
            ],
            "question": [
                "Check existing issues and discussions",
                "Consider asking on Stack Overflow"
            ]
        }
        return suggestions.get(category, [])
    
    def find_duplicates(self, title: str, existing_issues: List[Dict]) -> List[Dict]:
        """Find potentially duplicate issues"""
        duplicates = []
        title_words = set(re.findall(r'\w+', title.lower()))
        
        for issue in existing_issues:
            issue_title = issue.get("title", "")
            issue_words = set(re.findall(r'\w+', issue_title.lower()))
            
            common = title_words & issue_words
            if len(common) >= 3:
                duplicates.append({
                    "number": issue.get("number"),
                    "title": issue_title,
                    "similarity": len(common) / max(len(title_words), len(issue_words))
                })
        
        return sorted(duplicates, key=lambda x: x["similarity"], reverse=True)[:3]


def classify_issue(title: str, body: str = "") -> Dict:
    """Convenience function for classification"""
    classifier = IssueClassifier()
    return classifier.classify(title, body)
