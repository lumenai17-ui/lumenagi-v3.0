#!/usr/bin/env python3
"""
LumenAGI Dashboard v4.3 — Optimized Fullscreen Observatory
===========================================================

Mejoras v4.3:
- Sistema CPU/RAM/Disco (reemplaza GPU Processes)
- GPU Utilization con barra (como VRAM)
- Token Tracking emulado con datos realistas
- Cost Tracking emulado ($0 para Qwen local)
- Layout ajustado para mejor espaciado
"""

import json
import subprocess
import time
import psutil
import os
import random
from datetime import datetime
from pathlib import Path
from collections import deque
from flask import Flask, jsonify, send_from_directory, request, send_file
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lumenagi-v4-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = Path(__file__).parent

# Histórico de métricas
gpu_history = deque(maxlen=60)
agent_activity = {'kimi': deque(maxlen=60), 'qwen': deque(maxlen=60), 'api': deque(maxlen=60)}

# Token tracker con datos iniciales emulados (realistas para sesión)
token_tracker = {
    'kimi': {'input': 2847, 'output': 1923, 'cost': 0.0},
    'qwen': {'input': 45231, 'output': 28947, 'cost': 0.0},  # Local = mucho uso
    'gpt4o': {'input': 1245, 'output': 876, 'cost': 0.0}
}

# Incrementos por segundo (emulación realista)
token_rates = {
    'kimi': {'input': 3, 'output': 2},      # Coordinador intermitente
    'qwen': {'input': 45, 'output': 28},    # Trabajo constante local
    'gpt4o': {'input': 1, 'output': 1}      # API ocasional
}

# Estado SWARM
swarm_state = {
    'coordinator': {'active': False, 'task': None, 'vram_mb': 0, 'tokens_last_min': 0},
    'research': {'active': False, 'task': None, 'vram_mb': 0, 'tokens_last_min': 0},
    'build': {'active': False, 'task': None, 'vram_mb': 0, 'tokens_last_min': 0},
    'create': {'active': False, 'task': None, 'vram_mb': 0, 'tokens_last_min': 0}
}

traces = deque(maxlen=20)

def add_trace(agent, task, status, details=""):
    traces.append({'timestamp': datetime.now().isoformat(), 'agent': agent, 'task': task, 'status': status, 'details': details})

def get_gpu_metrics():
    """GPU metrics via nvidia-smi"""
    try:
        result = subprocess.run([
            'nvidia-smi', 
            '--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw,power.limit',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True, timeout=3)
        
        if result.returncode != 0:
            return None
            
        parts = result.stdout.strip().split(', ')
        device, used, total, util, temp, power, power_limit = parts
        
        return {
            'device': device,
            'used_mb': int(used),
            'total_mb': int(total),
            'utilization': int(util),
            'temperature': int(temp),
            'power_draw': float(power) if power != '[N/A]' else 0.0,
            'power_limit': float(power_limit) if power_limit != '[N/A]' else 0.0
        }
    except Exception as e:
        print(f"[GPU Error] {e}")
        return None

def get_ollama_models():
    """Loaded Ollama models"""
    try:
        result = subprocess.run(['curl', '-s', 'http://127.0.0.1:11434/api/ps'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return [{'name': m.get('name'), 'size': m.get('size', 0), 'vram': m.get('size_vram', 0), 'expires': m.get('expires_at', 'unknown')} for m in data.get('models', [])]
    except Exception as e:
        print(f"[Ollama Error] {e}")
    return []

def get_system_stats():
    """CPU, RAM, Disk stats"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu': {'percent': cpu_percent, 'cores': psutil.cpu_count()},
            'ram': {'used_gb': memory.used / (1024**3), 'total_gb': memory.total / (1024**3), 'percent': memory.percent},
            'disk': {'used_gb': disk.used / (1024**3), 'total_gb': disk.total / (1024**3), 'percent': (disk.used / disk.total) * 100}
        }
    except Exception as e:
        print(f"[System Error] {e}")
        return None

def get_network_traffic():
    """Network traffic"""
    try:
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
        }
    except:
        return None

def update_swarm_state():
    """Update SWARM states"""
    ollama_models = get_ollama_models()
    
    for model in ollama_models:
        if 'qwen' in model['name'].lower():
            swarm_state['build'].update({'active': True, 'vram_mb': model.get('vram', 20000)})
            swarm_state['create'].update({'active': True, 'vram_mb': model.get('vram', 20000)})
            swarm_state['research'].update({'active': True, 'vram_mb': 0})

def emulate_token_increments():
    """Emulate realistic token usage increments"""
    for agent in ['kimi', 'qwen', 'gpt4o']:
        # Variación aleatoria ±30%
        in_inc = int(token_rates[agent]['input'] * random.uniform(0.7, 1.3))
        out_inc = int(token_rates[agent]['output'] * random.uniform(0.7, 1.3))
        
        token_tracker[agent]['input'] += in_inc
        token_tracker[agent]['output'] += out_inc

def calculate_costs():
    """Calculate costs (Qwen is free)"""
    PRICES = {
        'kimi': {'input': 0.001, 'output': 0.003},     # $1-3/M tokens
        'qwen': {'input': 0.000, 'output': 0.000},     # $0 - Local!
        'gpt4o': {'input': 0.0025, 'output': 0.010}    # $2.5-10/M tokens
    }
    
    costs = {}
    for agent, data in token_tracker.items():
        price = PRICES.get(agent, {'input': 0, 'output': 0})
        costs[agent] = (data['input'] / 1000) * price['input'] + (data['output'] / 1000) * price['output']
    
    return costs

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@socketio.on('connect')
def handle_connect():
    print(f"[WS] Client connected: {datetime.now()}")
    emit('connected', {'status': 'connected', 'timestamp': datetime.now().isoformat()})

def emit_metrics():
    """Emit metrics every second"""
    last_net_io = None
    
    while True:
        try:
            # GPU metrics
            gpu = get_gpu_metrics()
            if gpu:
                gpu_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'utilization': gpu['utilization'],
                    'vram_pct': (gpu['used_mb'] / gpu['total_mb']) * 100,
                    'temperature': gpu['temperature'],
                    'power': gpu['power_draw']
                })
            
            # System stats (CPU/RAM/Disk)
            system_stats = get_system_stats()
            
            # Ollama models
            ollama = get_ollama_models()
            
            # Network
            net_io = get_network_traffic()
            net_speed = {'up': 0, 'down': 0}
            if last_net_io and net_io:
                net_speed = {
                    'up': net_io['bytes_sent'] - last_net_io['bytes_sent'],
                    'down': net_io['bytes_recv'] - last_net_io['bytes_recv']
                }
            last_net_io = net_io
            
            # Update SWARM
            update_swarm_state()
            
            # Emulate token increments
            emulate_token_increments()
            
            # Calculate costs
            costs = calculate_costs()
            
            # Agent activity
            if gpu:
                agent_activity['qwen'].append(gpu['utilization'])
                agent_activity['kimi'].append(5 + random.randint(-2, 2))
                agent_activity['api'].append(random.randint(0, 5))
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'gpu': gpu,
                'system': system_stats,
                'gpu_history': list(gpu_history),
                'ollama_models': ollama,
                'network': {
                    'speed_mbps': {
                        'up': round(net_speed['up'] * 8 / 1_000_000, 2),
                        'down': round(net_speed['down'] * 8 / 1_000_000, 2)
                    }
                },
                'swarm': swarm_state,
                'swarm_topology': {
                    'coordinator': {'name': 'Lumen', 'model': 'kimi-2.5', 'status': 'active' if swarm_state['coordinator']['active'] else 'idle'},
                    'workers': [
                        {'name': 'Research', 'model': 'gpt-4o', 'vram': swarm_state['research']['vram_mb'], 'active': swarm_state['research']['active']},
                        {'name': 'Build', 'model': 'qwen32', 'vram': swarm_state['build']['vram_mb'], 'active': swarm_state['build']['active']},
                        {'name': 'Create', 'model': 'qwen32', 'vram': swarm_state['create']['vram_mb'], 'active': swarm_state['create']['active']}
                    ]
                },
                'token_tracker': token_tracker,
                'costs': costs,
                'agent_activity': {
                    'kimi': list(agent_activity['kimi']),
                    'qwen': list(agent_activity['qwen']),
                    'api': list(agent_activity['api'])
                },
                'traces': list(traces)
            }
            
            socketio.emit('metrics', data)
            
            if gpu and system_stats:
                print(f"[EMIT] GPU:{gpu['utilization']}% CPU:{system_stats['cpu']['percent']:.0f}% RAM:{system_stats['ram']['percent']:.0f}% Tokens:{sum(t['input']+t['output'] for t in token_tracker.values()):,}")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"[EMIT Error] {e}")
            time.sleep(1)

# API endpoints
@app.route('/api/agent/start', methods=['POST'])
def agent_start():
    data = request.json
    agent = data.get('agent')
    task = data.get('task')
    if agent in swarm_state:
        swarm_state[agent].update({'active': True, 'task': task})
    add_trace(agent, task, 'running')
    return jsonify({'status': 'ok'})

@app.route('/api/agent/complete', methods=['POST'])
def agent_complete():
    data = request.json
    agent = data.get('agent')
    task = data.get('task')
    tokens_in = data.get('tokens_input', 0)
    tokens_out = data.get('tokens_output', 0)
    
    if agent in swarm_state:
        swarm_state[agent].update({'active': False, 'task': None})
    
    if agent == 'coordinator':
        token_tracker['kimi']['input'] += tokens_in
        token_tracker['kimi']['output'] += tokens_out
    elif agent == 'research':
        token_tracker['gpt4o']['input'] += tokens_in
        token_tracker['gpt4o']['output'] += tokens_out
    else:
        token_tracker['qwen']['input'] += tokens_in
        token_tracker['qwen']['output'] += tokens_out
    
    add_trace(agent, task, 'completed', f"Tokens: {tokens_in}/{tokens_out}")
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    from threading import Thread
    print("🚀 LumenAGI Dashboard v4.3 — Optimized Fullscreen Observatory")
    print("📡 SocketIO: http://127.0.0.1:8766")
    print("✨ System Stats | Emulated Token Cost | GPU Util Bar")
    
    Thread(target=emit_metrics, daemon=True).start()
    socketio.run(app, host='127.0.0.1', port=8766, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
