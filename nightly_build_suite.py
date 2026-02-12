#!/usr/bin/env python3
"""
Nightly Build Suite — 2 AM automation
Inspired by Moltbook community: "Ship while your users sleep"
"""

import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

def nightly_build():
    """Execute nightly automation tasks"""
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tasks": []
    }
    
    # 1. Git auto-commit pending changes
    try:
        os.chdir("/home/lumen/lumenagi-v3.0")
        status = subprocess.run(["git", "status", "--short"], capture_output=True, text=True)
        
        if status.stdout.strip():
            subprocess.run(["git", "add", "-A"], check=True)
            subprocess.run([
                "git", "commit", 
                "-m", f"Nightly build: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            ], check=True)
            subprocess.run(["git", "push"], check=True)
            
            results["tasks"].append({
                "task": "git_auto_commit",
                "status": "success",
                "details": f"Committed {len(status.stdout.strip().split(chr(10)))} files"
            })
        else:
            results["tasks"].append({
                "task": "git_auto_commit", 
                "status": "skipped",
                "details": "No pending changes"
            })
    except Exception as e:
        results["tasks"].append({"task": "git_auto_commit", "status": "error", "details": str(e)})
    
    # 2. Log rotation and cleanup
    try:
        log_dir = Path("/home/lumen/.openclaw/workspace/logs")
        if log_dir.exists():
            # Archive logs older than 3 days
            for log_file in log_dir.glob("*.log"):
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if (datetime.now() - mtime).days > 3:
                    archive_dir = log_dir / "archive"
                    archive_dir.mkdir(exist_ok=True)
                    
                    # Compress and move
                    subprocess.run(["gzip", str(log_file)], check=True)
                    gz_file = log_file.with_suffix(".log.gz")
                    gz_file.rename(archive_dir / gz_file.name)
            
            results["tasks"].append({"task": "log_cleanup", "status": "success"})
    except Exception as e:
        results["tasks"].append({"task": "log_cleanup", "status": "error", "details": str(e)})
    
    # 3. Dependency check (just check, don't auto-update)
    try:
        # Check for outdated pip packages
        result = subprocess.run(
            ["pip", "list", "--outdated", "--format=json"],
            capture_output=True, text=True, timeout=30
        )
        outdated = json.loads(result.stdout) if result.stdout else []
        
        critical_packages = ["requests", "flask", "numpy", "chromadb", "openai"]
        updates_needed = [p for p in outdated if p["name"].lower() in critical_packages]
        
        results["tasks"].append({
            "task": "dependency_check",
            "status": "success",
            "details": f"{len(outdated)} outdated, {len(updates_needed)} critical"
        })
        
        # Save for manual review
        if updates_needed:
            with open("/tmp/updates_needed.json", "w") as f:
                json.dump(updates_needed, f, indent=2)
    except Exception as e:
        results["tasks"].append({"task": "dependency_check", "status": "error", "details": str(e)})
    
    # 4. Prep overnight summary
    try:
        # Generate metrics for morning report
        metrics = {
            "qwen_status": "stable",
            "commits_today": 0,  # Will be calculated
            "github_repo": "lumenai17-ui/lumenagi-v3.0",
            "timestamp": datetime.now().isoformat()
        }
        
        with open("/tmp/overnight_metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)
        
        results["tasks"].append({"task": "summary_prep", "status": "success"})
    except Exception as e:
        results["tasks"].append({"task": "summary_prep", "status": "error", "details": str(e)})
    
    # Log results
    nightly_log = Path("/home/lumen/.openclaw/workspace/logs/nightly_builds.log")
    nightly_log.parent.mkdir(exist_ok=True)
    
    with open(nightly_log, "a") as f:
        f.write(f"{datetime.now().isoformat()}: {json.dumps(results)}\n")
    
    return results

if __name__ == "__main__":
    print(json.dumps(nightly_build(), indent=2))
