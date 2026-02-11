#!/usr/bin/env python3
"""
LumenAGI Dashboard v4.2 — Enhanced Realtime Observability
===========================================================

Mejoras:
- GPU Power draw visible
- GPU History con datos reales (histórico de 60s)
- Ollama Models: VRAM usado, tiempo restante
- GPU Processes: lista de procesos CUDA
- SWARM Topology: estado "en uso", VRAM por agente
- Token Tracking + Cost Tracking en tiempo real
- Network Traffic: subida/bajada en tiempo real
- Traces: mensajes de agentes en tiempo real
"""

import json
import subprocess
import time
import psutil
import os
from datetime import datetime
from pathlib import Path
from collections import deque
from flask import Flask, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lumenagi-v4-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = Path(__file__).parent

# Histórico de métricas (últimos 60 puntos = 1 minuto a 1s por punto)
gpu_history = deque(maxlen=60)
agent_activity = {
    'kimi': deque(maxlen=60),
    'qwen': deque(maxlen=60),
    'api': deque(maxlen=60)
}

# Tracking de tokens por agente (acumulativo)
token_tracker = {
    'kimi': {'input': 0, 'output': 0, 'cost': 0.0},
    'qwen': {'input': 0, 'output': 0, 'cost': 0.0},
    'gpt4o': {'input': 0, 'output': 0, 'cost': 0.0}
}

# Estado de agentes SWARM (simulado - se actualizaría con OpenClaw API real)
swarm_state = {
    'coordinator': {'active': False, 'task': None, 'vram_mb': 0, 'tokens_last_min': 0},
    'research': {'active': False, 'task': None, 'vram_mb': 0, 'tokens_last_min': 0},
    'build': {'active': False, 'task': None, 'vram_mb': 0, 'tokens_last_min': 0},
    'create': {'active': False, 'task': None, 'vram_mb': 0, 'tokens_last_min': 0}
}

# Traces recientes (últimos 20)
traces = deque(maxlen=20)

def add_trace(agent, task, status, details=""):
    """Agregar un trace para mostrar en el dashboard."""
    traces.append({
        'timestamp': datetime.now().isoformat(),
        'agent': agent,
        'task': task,
        'status': status,  # 'running', 'completed', 'error'
        'details': details
    })

def get_gpu_metrics():
    """Get GPU metrics via nvidia-smi"""
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

def get_gpu_processes():
    """Get GPU processes using nvidia-smi"""
    try:
        result = subprocess.run([
            'nvidia-smi',
            '--query-compute-apps=pid,name,used_memory',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True, timeout=3)
        
        if result.returncode != 0:
            return []
        
        processes = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                parts = line.split(', ')
                if len(parts) >= 3:
                    processes.append({
                        'pid': parts[0],
                        'name': parts[1],
                        'vram_mb': int(parts[2])
                    })
        return processes
    except Exception as e:
        print(f"[GPU Procs Error] {e}")
        return []

def get_ollama_models():
    """Get loaded Ollama models with details"""
    try:
        result = subprocess.run(['curl', '-s', 'http://127.0.0.1:11434/api/ps'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            models = []
            for m in data.get('models', []):
                models.append({
                    'name': m.get('name'),
                    'size': m.get('size', 0),
                    'vram': m.get('size_vram', 0),
                    'expires': m.get('expires_at', 'unknown')
                })
            return models
    except Exception as e:
        print(f"[Ollama Error] {e}")
    return []

def get_network_traffic():
    """Get network traffic stats"""
    try:
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'err_in': net_io.errin,
            'err_out': net_io.errout
        }
    except:
        return None

def update_swarm_state():
    """Update SWARM agent states based on current GPU usage"""
    gpu_procs = get_gpu_processes()
    ollama_models = get_ollama_models()
    
    # Qwen usa VRAM cuando está cargado
    for model in ollama_models:
        if 'qwen' in model['name'].lower():
            swarm_state['build']['active'] = True
            swarm_state['build']['vram_mb'] = model.get('vram', 20000)
            swarm_state['create']['active'] = True
            swarm_state['create']['vram_mb'] = model.get('vram', 20000)
            swarm_state['research']['active'] = True
            swarm_state['research']['vram_mb'] = 0  # Qwen no VRAM para research
    
    # Simulación: si hay procesos de Python con alta VRAM, podría ser agente activo
    total_vram = sum(p['vram_mb'] for p in gpu_procs)
    swarm_state['coordinator']['active'] = total_vram > 1000

def calculate_costs():
    """Calculate costs based on token usage"""
    # Precios aproximados por 1K tokens
    PRICES = {
        'kimi': {'input': 0.001, 'output': 0.003},  # $1-3 por millón
        'qwen': {'input': 0.0, 'output': 0.0},      # Local = $0
        'gpt4o': {'input': 0.0025, 'output': 0.01}  # $2.5-10 por millón
    }
    
    costs = {}
    for agent, data in token_tracker.items():
        price = PRICES.get(agent, {'input': 0, 'output': 0})
        input_cost = (data['input'] / 1000) * price['input']
        output_cost = (data['output'] / 1000) * price['output']
        costs[agent] = input_cost + output_cost
    
    return costs

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index_v4.2.html')

@socketio.on('connect')
def handle_connect():
    print(f"[WS] Client connected: {datetime.now()}")
    emit('connected', {'status': 'connected', 'timestamp': datetime.now().isoformat()})

def emit_metrics():
    """Background thread: emit metrics every 1 second"""
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
            
            # Ollama models
            ollama = get_ollama_models()
            
            # GPU processes
            gpu_procs = get_gpu_processes()
            
            # Network traffic
            net_io = get_network_traffic()
            net_speed = {'up': 0, 'down': 0}
            if last_net_io and net_io:
                net_speed = {
                    'up': net_io['bytes_sent'] - last_net_io['bytes_sent'],
                    'down': net_io['bytes_recv'] - last_net_io['bytes_recv']
                }
            last_net_io = net_io
            
            # Update SWARM state
            update_swarm_state()
            
            # Calculate costs
            costs = calculate_costs()
            
            # Agent activity (simulado con GPU utilization por ahora)
            if gpu:
                agent_activity['qwen'].append(gpu['utilization'])
                agent_activity['kimi'].append(5)  # Cloud, poco uso local
                agent_activity['api'].append(0)
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'gpu': gpu,
                'gpu_history': list(gpu_history),
                'ollama_models': ollama,
                'gpu_processes': gpu_procs,
                'network': {
                    'current': net_io,
                    'speed_bytes': net_speed,
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
            
            if gpu:
                print(f"[EMIT] GPU: {gpu['utilization']}% | VRAM: {gpu['used_mb']/1024:.1f}GB | Power: {gpu['power_draw']:.0f}W | Net: ↑{net_speed['up']/1024:.0f}KB ↓{net_speed['down']/1024:.0f}KB")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"[EMIT Error] {e}")
            time.sleep(1)

# API endpoints para que los agentes reporten su actividad
@app.route('/api/agent/start', methods=['POST'])
def agent_start():
    """Agente reporta inicio de tarea"""
    data = request.json
    agent = data.get('agent')
    task = data.get('task')
    
    if agent in swarm_state:
        swarm_state[agent]['active'] = True
        swarm_state[agent]['task'] = task
    
    add_trace(agent, task, 'running')
    return jsonify({'status': 'ok'})

@app.route('/api/agent/complete', methods=['POST'])
def agent_complete():
    """Agente reporta fin de tarea"""
    data = request.json
    agent = data.get('agent')
    task = data.get('task')
    tokens_in = data.get('tokens_input', 0)
    tokens_out = data.get('tokens_output', 0)
    
    if agent in swarm_state:
        swarm_state[agent]['active'] = False
        swarm_state[agent]['task'] = None
    
    # Actualizar token tracker
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
    print("🚀 LumenAGI Dashboard v4.2 — Enhanced Observability")
    print("📡 SocketIO: http://127.0.0.1:8766")
    print("✨ Features: GPU History | Token Tracking | Network Traffic | SWARM Status")
    
    # Start background emitter
    Thread(target=emit_metrics, daemon=True).start()
    
    socketio.run(app, host='127.0.0.1', port=8766, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
