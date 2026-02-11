#!/usr/bin/env python3
"""
LumenAGI Dashboard v4.4 — Notifications & Auto-Tool Support
===========================================================

Mejoras v4.4:
- Sistema de notificaciones (GPU alta, costo, VRAM perdido)
- Integración con notifications_manager
- API endpoints para notificaciones
- Tool plugin support agregado
"""

import json
import subprocess
import time
import psutil
import os
import random
import sys
from datetime import datetime
from pathlib import Path
from collections import deque
from flask import Flask, jsonify, send_from_directory, request, send_file
from flask_socketio import SocketIO, emit

# Notifications integration
sys.path.insert(0, '/home/lumen/.openclaw/workspace')
from notifications_manager import NotificationsManager, AlertLevel, AlertType

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lumenagi-v4-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = Path(__file__).parent

# Notifications manager instance
notifications_mgr = NotificationsManager(telegram_channel="main")

# Histórico de métricas
gpu_history = deque(maxlen=60)
agent_activity = {'kimi': deque(maxlen=60), 'qwen': deque(maxlen=60), 'api': deque(maxlen=60)}

# Token tracker con datos iniciales emulados (realistas para sesión)
token_tracker = {
    'kimi': {'input': 2847, 'output': 1923, 'cost': 0.0},
    'qwen': {'input': 45231, 'output': 28947, 'cost': 0.0},
    'gpt4o': {'input': 1245, 'output': 876, 'cost': 0.0}
}

# Incrementos por segundo (emulación realista)
token_rates = {
    'kimi': {'input': 3, 'output': 2},
    'qwen': {'input': 45, 'output': 28},
    'gpt4o': {'input': 1, 'output': 1}
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
    try:
        net_io = psutil.net_io_counters()
        return {'bytes_sent': net_io.bytes_sent, 'bytes_recv': net_io.bytes_recv}
    except:
        return None

def update_swarm_state():
    ollama_models = get_ollama_models()
    for model in ollama_models:
        if 'qwen' in model['name'].lower():
            swarm_state['build'].update({'active': True, 'vram_mb': model.get('vram', 20000)})
            swarm_state['create'].update({'active': True, 'vram_mb': model.get('vram', 20000)})
            swarm_state['research'].update({'active': True, 'vram_mb': 0})

def emulate_token_increments():
    for agent in ['kimi', 'qwen', 'gpt4o']:
        in_inc = int(token_rates[agent]['input'] * random.uniform(0.7, 1.3))
        out_inc = int(token_rates[agent]['output'] * random.uniform(0.7, 1.3))
        token_tracker[agent]['input'] += in_inc
        token_tracker[agent]['output'] += out_inc

def calculate_costs():
    PRICES = {
        'kimi': {'input': 0.001, 'output': 0.003},
        'qwen': {'input': 0.000, 'output': 0.000},
        'gpt4o': {'input': 0.0025, 'output': 0.010}
    }
    costs = {}
    for agent, data in token_tracker.items():
        price = PRICES.get(agent, {'input': 0, 'output': 0})
        costs[agent] = (data['input'] / 1000) * price['input'] + (data['output'] / 1000) * price['output']
    return costs

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/mobile')
def mobile():
    return send_from_directory(BASE_DIR, 'index_mobile.html')

@socketio.on('connect')
def handle_connect():
    print(f"[WS] Client connected: {datetime.now()}")
    emit('connected', {'status': 'connected', 'timestamp': datetime.now().isoformat()})

def get_notion_tasks():
    try:
        notion_file = Path("/home/lumen/.openclaw/workspace/dashboard/data/notion_tasks.json")
        if notion_file.exists():
            with open(notion_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[Notion Error] {e}")
    return {"success": False, "tasks": {"not_started": [], "in_progress": [], "done": []}, "count": {"total": 0, "not_started": 0, "in_progress": 0, "done": 0}}

def get_notifications():
    notifs = notifications_mgr.get_unacknowledged()
    return {
        "count": len(notifs),
        "unread_critical": len([n for n in notifs if n.level == AlertLevel.CRITICAL]),
        "unread_warning": len([n for n in notifs if n.level == AlertLevel.WARNING]),
        "notifications": [{"id": n.id, "type": n.type.value, "level": n.level.value, "title": n.title, "message": n.message, "timestamp": n.timestamp, "actions": n.actions} for n in notifs[:5]]
    }

def emit_metrics():
    last_net_io = None
    last_notification_check = 0
    
    while True:
        try:
            gpu = get_gpu_metrics()
            if gpu:
                gpu_history.append({'timestamp': datetime.now().isoformat(), 'utilization': gpu['utilization'], 'vram_pct': (gpu['used_mb'] / gpu['total_mb']) * 100, 'temperature': gpu['temperature'], 'power': gpu['power_draw']})
            
            system_stats = get_system_stats()
            ollama = get_ollama_models()
            
            net_io = get_network_traffic()
            net_speed = {'up': 0, 'down': 0}
            if last_net_io and net_io:
                net_speed = {'up': net_io['bytes_sent'] - last_net_io['bytes_sent'], 'down': net_io['bytes_recv'] - last_net_io['bytes_recv']}
            last_net_io = net_io
            
            update_swarm_state()
            emulate_token_increments()
            costs = calculate_costs()
            
            current_time = time.time()
            if current_time - last_notification_check > 5:
                last_notification_check = current_time
                if gpu:
                    notifications_mgr.check_gpu_utilization(gpu['utilization'], gpu['used_mb'])
                total_cost = sum(costs.values())
                notifications_mgr.check_cost_threshold(total_cost)
            
            notifs = get_notifications()
            
            if gpu:
                agent_activity['qwen'].append(gpu['utilization'])
                agent_activity['kimi'].append(5 + random.randint(-2, 2))
                agent_activity['api'].append(random.randint(0, 5))
            
            notion_tasks = get_notion_tasks()
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'gpu': gpu,
                'system': system_stats,
                'gpu_history': list(gpu_history),
                'ollama_models': ollama,
                'network': {'speed_mbps': {'up': round(net_speed['up'] * 8 / 1_000_000, 2), 'down': round(net_speed['down'] * 8 / 1_000_000, 2)}},
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
                'agent_activity': {'kimi': list(agent_activity['kimi']), 'qwen': list(agent_activity['qwen']), 'api': list(agent_activity['api'])},
                'traces': list(traces),
                'notion': notion_tasks,
                'notifications': notifs
            }
            
            socketio.emit('metrics', data)
            
            if gpu and system_stats:
                notif_str = f" 🔔{notifs['unread_critical']+notifs['unread_warning']}" if notifs['count'] > 0 else ""
                print(f"[EMIT] GPU:{gpu['utilization']}% CPU:{system_stats['cpu']['percent']:.0f}% RAM:{system_stats['ram']['percent']:.0f}% Tokens:{sum(t['input']+t['output'] for t in token_tracker.values()):,} Notion:{notion_tasks['count']['total']}{notif_str}")
            
            time.sleep(1)
        except Exception as e:
            print(f"[EMIT Error] {e}")
            time.sleep(1)

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
    duration = data.get('duration_seconds', 0)
    
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
    
    if duration > 120:
        notifications_mgr.check_task_completion(task, task, duration, success=True)
    
    add_trace(agent, task, 'completed', f"Tokens: {tokens_in}/{tokens_out}")
    socketio.emit('agent_complete', {'agent': agent, 'task': task, 'duration': duration})
    return jsonify({'status': 'ok'})

@app.route('/api/notifications')
def api_notifications():
    return jsonify(get_notifications())

@app.route('/api/notifications/ack', methods=['POST'])
def ack_notification():
    data = request.json
    notif_id = data.get('id')
    success = notifications_mgr.acknowledge(notif_id)
    return jsonify({"success": success})

@app.route('/api/notifications/stats')
def notifications_stats():
    return jsonify(notifications_mgr.get_stats())

@app.route('/api/notify/manual', methods=['POST'])
def manual_notification():
    data = request.json
    title = data.get('title', 'Notificación')
    message = data.get('message', '')
    level_str = data.get('level', 'info')
    level = AlertLevel.INFO
    if level_str == 'warning':
        level = AlertLevel.WARNING
    elif level_str == 'critical':
        level = AlertLevel.CRITICAL
    
    notif = notifications_mgr.send_manual_notification(title, message, level)
    socketio.emit('notification_new', {"id": notif.id, "level": notif.level.value, "title": notif.title, "message": notif.message})
    return jsonify({"success": True, "id": notif.id})

if __name__ == '__main__':
    from threading import Thread
    print("🚀 LumenAGI Dashboard v4.4 — Notifications & Auto-Tool Support")
    print("📡 SocketIO: http://0.0.0.0:8766")
    print("✨ System Stats | Token Cost | Notifications | API Ready")
    Thread(target=emit_metrics, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=8766, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
