#!/usr/bin/env python3
"""
Security Verification Suite - Checksums & Integrity
"Skill.md is unsigned binary" - Community insight from Moltbook
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime

CRITICAL_FILES = {
    "workspace/coordinator_swarm.py": "coordinator_swarm.py",
    "workspace/coordinator_rag_optimized.py": "coordinator_rag_optimized.py",
    "workspace/nightly_build_suite.py": "nightly_build_suite.py",
    "workspace/deepbook_editor_v1.py": "deepbook_editor_v1.py",
    "workspace/gmail_inbox_reader.py": "gmail_inbox_reader.py",
    "scripts/keepalive-qwen32b.sh": "keepalive-qwen32b.sh"
}

def calculate_checksum(filepath):
    """Calculate SHA-256 checksum of file"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_integrity():
    """Verify integrity of critical files"""
    base_path = Path("/home/lumen/.openclaw")
    workspace = base_path / "workspace"
    manifest_path = workspace / "security_manifest.json"
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "files_checked": [],
        "verified": [],
        "changed": [],
        "missing": []
    }
    
    # Load existing manifest or create new
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
    else:
        manifest = {}
    
    for relative_path, display_name in CRITICAL_FILES.items():
        filepath = base_path / relative_path
        
        if not filepath.exists():
            results["missing"].append(display_name)
            continue
        
        current_hash = calculate_checksum(filepath)
        results["files_checked"].append(display_name)
        
        if relative_path in manifest:
            if manifest[relative_path] == current_hash:
                results["verified"].append(display_name)
            else:
                results["changed"].append({
                    "file": display_name,
                    "expected": manifest[relative_path][:16] + "...",
                    "actual": current_hash[:16] + "..."
                })
        else:
            # New file, add to manifest
            manifest[relative_path] = current_hash
            results["verified"].append(f"{display_name} (new)")
    
    # Save updated manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return results

if __name__ == "__main__":
    result = verify_integrity()
    print(json.dumps(result, indent=2))
