#!/usr/bin/env python3
"""LumenAGI Mission Control Backend API + Static Server"""

import subprocess
import json
import os
from datetime import datetime
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)

WORKSPACE = "/home/lumen/.openclaw/workspace"
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))

def get_gpu_stats():
    """Get real-time GPU stats from nvidia-smi"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.free,utilization.gpu,temperature.gpu', 
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        used, free, util, temp = result.stdout.strip().split(', ')
        return {
            "used_mb": int(used),
            "free_mb": int(free),
            "used_gb": round(int(used) / 1024, 1),
            "free_gb": round(int(free) / 1024, 1),
            "total_gb": 24,
            "utilization": int(util),
            "temperature": int(temp)
        }
    except Exception as e:
        return {"error": str(e), "used_gb": 0.5, "free_gb": 23.5}

def get_agents_status():
    """Get agent status from OpenClaw agent configs"""
    agents = []
    agents_dir = "/home/lumen/.openclaw/agents"
    
    agent_configs = {
        "main": {"name": "Lumen", "role": "Coordinator", "status": "active"},
        "research-qwen32": {"name": "Research", "role": "Information", "status": "idle"},
        "build-qwen32": {"name": "Build", "role": "Execution", "status": "idle"},
        "create-qwen32": {"name": "Create", "role": "Media Gen", "status": "idle"},
    }
    
    for agent_dir, config in agent_configs.items():
        config_path = os.path.join(agents_dir, agent_dir, "agent", "openclaw.json")
        model = "unknown"
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    model = data.get("model", "unknown")
                    # Simplify model name for display
                    if "kimi" in model.lower():
                        model = "kimi-2.5"
                    elif "qwen2.5:32b" in model.lower():
                        model = "qwen-32b"
                    elif "qwen" in model.lower():
                        model = "qwen"
        except Exception:
            pass
        
        agents.append({
            "name": config["name"],
            "role": config["role"],
            "status": config["status"],
            "model": model,
            "full_name": agent_dir
        })
    
    return agents

def get_recent_activity():
    """Get recent activity"""
    return [
        {"icon": "🔥", "text": "Qwen 14b unloaded from GPU", "time": "10:09"},
        {"icon": "✅", "text": "Mission Control dashboard created", "time": "09:45"},
        {"icon": "🔍", "text": "Research: Dashboard best practices", "time": "09:30"},
        {"icon": "🔨", "text": "Build: Created SWARM agent workspaces", "time": "09:25"},
        {"icon": "🦞", "text": "Moltbook account claimed", "time": "09:20"},
        {"icon": "🧹", "text": "Workspace cleanup completed", "time": "09:15"},
    ]

def get_system_status():
    """Get overall system status"""
    return {
        "model": "kimi-2.5",
        "provider": "Ollama Cloud",
        "gateway": "127.0.0.1:18789",
        "heartbeat": "30 min",
        "channels": ["Telegram", "Moltbook"],
        "moltbook": "https://moltbook.com/u/LumenAGI",
        "local_model": "qwen2.5:32b",
        "gpu_vram": "20GB"
    }

# API Endpoints
@app.route('/api/gpu')
def gpu():
    return jsonify(get_gpu_stats())

@app.route('/api/agents')
def agents():
    return jsonify(get_agents_status())

@app.route('/api/activity')
def activity():
    return jsonify(get_recent_activity())

@app.route('/api/status')
def status():
    return jsonify(get_system_status())

@app.route('/api/all')
def all_data():
    return jsonify({
        "gpu": get_gpu_stats(),
        "agents": get_agents_status(),
        "activity": get_recent_activity(),
        "status": get_system_status(),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# Serve static files
@app.route('/')
def index():
    return send_from_directory(DASHBOARD_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(DASHBOARD_DIR, filename)

if __name__ == '__main__':
    print("🚀 LumenAGI Mission Control: http://127.0.0.1:8765")
    print("📊 API endpoints:")
    print("   - http://127.0.0.1:8765/api/gpu")
    print("   - http://127.0.0.1:8765/api/agents")
    print("   - http://127.0.0.1:8765/api/all")
    app.run(host='127.0.0.1', port=8765, debug=False)
