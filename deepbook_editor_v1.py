#!/usr/bin/env python3
"""
DeepBook Editor v1.0 — AI-powered document editor
Features: Markdown support, real-time preview, AI assistance
"""

import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

class DeepBookEditor:
    """Lightweight markdown editor with AI features"""
    
    def __init__(self, workspace_path: str = "/home/lumen/lumen/"):
        self.workspace = Path(workspace_path)
        self.workspace.mkdir(exist_ok=True)
        self.current_doc = None
        self.history = []
        
    def create_document(self, title: str, template: str = "blank") -> Dict:
        """Create new document with optional template"""
        
        templates = {
            "blank": "",
            "report": "# Report: {title}\n\n## Summary\n\n## Key Points\n\n## Conclusion\n",
            "tutorial": "# Tutorial: {title}\n\n## Overview\n\n## Step 1\n\n## Step 2\n\n## Conclusion\n",
            "note": "# Note: {title}\n\nDate: {date}\n\n## Content\n"
        }
        
        content = templates.get(template, "").format(
            title=title,
            date=datetime.now().strftime("%Y-%m-%d")
        )
        
        doc_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{title[:20]}"
        doc_path = self.workspace / f"{doc_id}.md"
        
        doc_data = {
            "id": doc_id,
            "title": title,
            "content": content,
            "template": template,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "word_count": len(content.split()),
            "path": str(doc_path)
        }
        
        # Save to file
        doc_path.write_text(content, encoding='utf-8')
        
        self.current_doc = doc_data
        self.history.append({"action": "create", "doc_id": doc_id, "time": datetime.now().isoformat()})
        
        return doc_data
    
    def edit_document(self, doc_id: str, new_content: str) -> Dict:
        """Edit existing document"""
        doc_path = self.workspace / f"{doc_id}.md"
        
        if not doc_path.exists():
            return {"error": "Document not found"}
        
        # Backup current version
        backup_path = self.workspace / f"{doc_id}_backup_{datetime.now().strftime('%H%M%S')}.md"
        backup_path.write_text(doc_path.read_text(), encoding='utf-8')
        
        # Write new content
        doc_path.write_text(new_content, encoding='utf-8')
        
        doc_data = {
            "id": doc_id,
            "content": new_content,
            "word_count": len(new_content.split()),
            "modified": datetime.now().isoformat(),
            "backup": str(backup_path)
        }
        
        self.history.append({"action": "edit", "doc_id": doc_id, "time": datetime.now().isoformat()})
        
        return doc_data
    
    def list_documents(self) -> list:
        """List all documents in workspace"""
        docs = []
        for md_file in self.workspace.glob("*.md"):
            if "_backup_" not in md_file.name:
                content = md_file.read_text(encoding='utf-8')
                docs.append({
                    "filename": md_file.name,
                    "title": content.split("\n")[0].replace("# ", "").strip() if content.startswith("#") else md_file.name,
                    "size": len(content),
                    "words": len(content.split())
                })
        return docs
    
    def ai_assist(self, content: str, operation: str = "improve") -> str:
        """Placeholder for AI assistance (integrates with Qwen)"""
        
        operations = {
            "improve": "# Improved version:\n\n" + content,
            "summarize": "# Summary:\n\n" + "\n".join(["- " + line for line in content.split("\n")[:3]]),
            "expand": content + "\n\n## Additional Context\n\n[AI would expand this section based on content]",
            "format": content  # Already formatted
        }
        
        return operations.get(operation, content)

# CLI interface
if __name__ == "__main__":
    import sys
    
    editor = DeepBookEditor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            docs = editor.list_documents()
            print(f"📚 Documents ({len(docs)}):")
            for doc in docs:
                print(f"  • {doc['title']} ({doc['words']} words)")
        
        elif sys.argv[1] == "--create" and len(sys.argv) > 2:
            template = sys.argv[3] if len(sys.argv) > 3 else "blank"
            doc = editor.create_document(sys.argv[2], template)
            print(f"✅ Created: {doc['id']} ({doc['word_count']} words)")
        
        else:
            print("Usage:")
            print("  python3 deepbook_editor_v1.py --list")
            print("  python3 deepbook_editor_v1.py --create 'Title' [template]")
    else:
        # Demo mode
        doc = editor.create_document("Welcome to DeepBook", "note")
        print(f"🚀 DeepBook Editor v1.0")
        print(f"✅ Demo document created: {doc['id']}")
        print(f"📁 Workspace: {editor.workspace}")
