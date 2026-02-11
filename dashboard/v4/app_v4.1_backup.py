#!/usr/bin/env python3
"""
LumenAGI Dashboard v4.1 — Simplified Realtime (Flask-SocketIO)
"""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lumenagi-v4-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = Path(__file__).parent

def get_gpu_metrics():
    """Get GPU metrics via nvidia-smi"""
    try:
        result = subprocess.run([
            'nvidia-smi', 
            '--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True, timeout=3)
        
        if result.returncode != 0:
            return None
            
        parts = result.stdout.strip().split(', ')
        device, used, total, util, temp, power = parts
        
        return {
            'device': device,
            'used_mb': int(used),
            'total_mb': int(total),
            'utilization': int(util),
            'temperature': int(temp),
            'power_draw': float(power) if power != '[N/A]' else 0.0
        }
    except Exception as e:
        print(f"GPU error: {e}")
        return None

def get_ollama_models():
    """Get loaded Ollama models"""
    try:
        result = subprocess.run(['curl', '-s', 'http://127.0.0.1:11434/api/ps'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return [m.get('name') for m in data.get('models', [])]
    except:
        pass
    return []

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@socketio.on('connect')
def handle_connect():
    print(f"[WS] Client connected: {datetime.now()}")
    emit('connected', {'status': 'connected', 'timestamp': datetime.now().isoformat()})

def emit_metrics():
    """Background thread: emit metrics every 1 second"""
    while True:
        try:
            gpu = get_gpu_metrics()
            ollama = get_ollama_models()
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'gpu': gpu,
                'ollama_models': ollama,
                'swarm': {
                    'coordinator': 'main',
                    'workers': ['research-qwen32', 'build-qwen32', 'create-qwen32']
                }
            }
            
            socketio.emit('metrics', data)
            print(f"[EMIT] GPU: {gpu['utilization'] if gpu else 'N/A'}%, Ollama: {len(ollama)} models")
            time.sleep(1)  # 1 second update rate
        except Exception as e:
            print(f"[EMIT] Error: {e}")
            time.sleep(1)

if __name__ == '__main__':
    from threading import Thread
    print("🚀 LumenAGI Dashboard v4.1 — Simplified WebSocket")
    print("📡 SocketIO: http://127.0.0.1:8766")
    
    # Start background emitter
    Thread(target=emit_metrics, daemon=True).start()
    
    socketio.run(app, host='127.0.0.1', port=8766, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
