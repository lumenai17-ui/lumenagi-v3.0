#!/usr/bin/env python3
"""
Enhanced Tool Detection — v2.0 with more patterns and confidence scoring
Added: git, docker, sql, api, deploy patterns
"""

import re
from typing import Dict, List, Tuple

# Enhanced patterns with confidence scores
TOOL_PATTERNS = {
    "git": {
        "patterns": [
            r"\bgit\s+(clone|commit|push|pull|branch|merge|status|log|add)",
            r"\b(gitHub|gitlab|bitbucket)\b",
            r"\b\.git\b",
        ],
        "confidence": 0.9,
        "keywords": ["version control", "repository", "commit", "branch"]
    },
    "docker": {
        "patterns": [
            r"\bdocker\s+(build|run|ps|exec|compose|image|container)",
            r"\b(dockerfile|docker-compose\.yml)\b",
            r"\bcontaineriz",
        ],
        "confidence": 0.85,
        "keywords": ["container", "image", "virtualization", "deployment"]
    },
    "sql": {
        "patterns": [
            r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\s+.*\b(FROM|TABLE|INTO)\b",
            r"\b(database|query|schema|migration)\b",
            r"\b(postgres|mysql|sqlite|mongodb)\b",
        ],
        "confidence": 0.88,
        "keywords": ["database", "query", "table", "migration"]
    },
    "api": {
        "patterns": [
            r"\b(GET|POST|PUT|DELETE|PATCH)\s+/\w+",
            r"\b(endpoint|route|handler|middleware)\b",
            r"\b(REST|GraphQL|API)\s+",
        ],
        "confidence": 0.82,
        "keywords": ["endpoint", "request", "response", "json"]
    },
    "deploy": {
        "patterns": [
            r"\b(deploy|deployment|production|prod|release)\b",
            r"\b(vercel|netlify|heroku|aws|gcp|azure)\b",
            r"\b(CI/CD|pipeline|github\s+actions)\b",
        ],
        "confidence": 0.8,
        "keywords": ["hosting", "server", "production", "release"]
    },
}

def detect_tools(text: str) -> List[Tuple[str, float]]:
    """Detect tools with confidence scores"""
    text_lower = text.lower()
    detected = []
    
    for tool, config in TOOL_PATTERNS.items():
        score = 0.0
        
        # Check regex patterns
        for pattern in config["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                score += config["confidence"]
                break
        
        # Check keywords (boost confidence)
        keyword_matches = sum(1 for kw in config["keywords"] if kw in text_lower)
        if keyword_matches >= 2:
            score += 0.15
        
        if score > 0.5:
            detected.append((tool, min(score, 1.0)))
    
    # Sort by confidence
    detected.sort(key=lambda x: x[1], reverse=True)
    return detected

# Backward compatible interface
def detect_tool_confidence(text: str) -> Dict[str, float]:
    """Return dict of tool->confidence for existing code"""
    detected = detect_tools(text)
    return {tool: conf for tool, conf in detected}
