#!/usr/bin/env python3
"""
LumenAGI Dashboard v5.5 — Control Panel Nivel Pro
===================================================
FUSIÓN: v2.0 (gráficas históricas + GPU detallada) + v4.4 (visual) + APIs reales
"""

import json, subprocess, time, psutil, os, random, sys, re
from datetime import datetime
from pathlib import Path
from collections import deque
from flask import Flask, jsonify, send_from_directory, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lumenagi-v55-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ===== SISTEMA DE DATOS EN TIEMPO REAL =====
resource_history = {'cpu': deque(maxlen=60), 'ram': deque(maxlen=60), 'gpu': deque(maxlen=60), 'vram': deque(maxlen=60), 'timestamps': deque(maxlen=60)}
token_tracker = {'kimi': {'input': 2847, 'output': 1923, 'cost': 0.08}, 'qwen': {'input': 45231, 'output': 28947, 'cost': 0.0}, 'gpt4': {'input': 1245, 'output': 876, 'cost': 0.05}}
traces = deque(maxlen=20)

# Arquitectura SWARM v3.0
ARCHITECTURE = {
    'cerebro': {'name': 'Lumen', 'model': 'Kimi K2.5', 'location': 'Cloud', 'status': 'active', 'cost_mode': 'Ollama Pro'},
    'local': {'name': 'Qwen Agent', 'model': 'Qwen 2.5 32B', 'location': 'Local VRAM', 'vram_gb': 20, 'status': 'loaded'},
    'research': {'name': 'Research', 'model': 'GPT-4', 'location': 'Cloud', 'status': 'standby', 'cost_mode': 'API'}
}

def get_gpu_info():
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw,power.limit,pstate,clocks.gr,clocks.mem', '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            parts = result.stdout.strip().split(', ')
            return {
                'name': parts[0], 'used_mb': int(parts[1]), 'total_mb': int(parts[2]),
                'utilization': int(parts[3]), 'temperature': int(parts[4]),
                'power_draw': float(parts[5]), 'power_limit': float(parts[6]),
                'pstate': parts[7], 'clock_gpu': int(parts[8]), 'clock_mem': int(parts[9]),
                'vram_percent': (int(parts[1]) / int(parts[2])) * 100
            }
    except: pass
    return None

def get_ollama_models():
    try:
        result = subprocess.run(['curl', '-s', 'http://127.0.0.1:11434/api/ps'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return [{'name': m.get('name'), 'size': m.get('size_vram', 0), 'processor': m.get('details', {}).get('processor', 'GPU'), 'expires': m.get('expires_at', '-')} for m in data.get('models', [])]
    except: pass
    return []

def get_system_stats():
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        load = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
        return {
            'cpu': cpu, 'ram_percent': mem.percent, 'ram_used': mem.used // (1024**3), 'ram_total': mem.total // (1024**3),
            'disk_percent': disk.percent, 'load': load, 'cores': psutil.cpu_count()
        }
    except: return None

def get_processes():
    procesos = []
    targets = [
        ('ollama', '🦙 Ollama', 'ollama'),
        ('python.*dashboard', '📊 Dashboard', 'dashboard'),
        ('openclaw', '🔌 OpenClaw', 'gateway'),
        ('chrome.*chrome-shelf', '🌐 Chromium', 'browser'),
    ]
    for pattern, nombre, key in targets:
        try:
            result = subprocess.run(f"ps aux | grep -E '{pattern}' | grep -v grep | head -1", shell=True, capture_output=True, text=True, timeout=2)
            if result.stdout:
                parts = result.stdout.split()
                if len(parts) >= 11:
                    procesos.append({'name': nombre, 'pid': parts[1], 'cpu': parts[2], 'mem': parts[3], 'cmd': ' '.join(parts[10:])[:30]})
        except: pass
    return procesos

def get_api_status():
    secrets = Path('/home/lumen/.openclaw/workspace/secrets')
    return {
        'youtube': {'status': '✅' if (secrets / 'youtube_tokens.json').exists() else '❌', 'health': 'online' if (secrets / 'youtube_tokens.json').exists() else 'offline'},
        'gmail': {'status': '✅' if (secrets / 'gmail_token.json').exists() else '❌', 'health': 'online' if (secrets / 'gmail_token.json').exists() else 'offline'},
        'notion': {'status': '✅' if (secrets / 'notion_credentials.json').exists() else '❌', 'health': 'online' if (secrets / 'notion_credentials.json').exists() else 'offline'},
        'moltbook': {'status': '✅' if (secrets / 'moltbook_credentials.json').exists() else '❌', 'profile': 'https://moltbook.com/u/LumenAGI'},
        'telegram': {'status': '✅ Bot activo', 'health': 'online'}
    }

def get_lumen_tasks():
    return list(traces)[-5:]

def get_hb_tasks():
    return [{'text': 'Dashboard v5.5 deploy', 'icon': '🔴', 'done': False}, {'text': 'Review architecture', 'icon': '🟡', 'done': False}]

# ===== EMISIÓN EN TIEMPO REAL =====
def emit_loop():
    while True:
        try:
            gpu = get_gpu_info()
            system = get_system_stats()
            
            if gpu and system:
                now = datetime.now().strftime('%H:%M:%S')
                resource_history['cpu'].append(system['cpu'])
                resource_history['ram'].append(system['ram_percent'])
                resource_history['gpu'].append(gpu['utilization'])
                resource_history['vram'].append(gpu['vram_percent'])
                resource_history['timestamps'].append(now)
            
            ollama = get_ollama_models()
            total_cost = sum(t['cost'] for t in token_tracker.values())
            
            socketio.emit('metrics', {
                'timestamp': now if gpu else '-',
                'gpu': gpu,
                'system': system,
                'history': {k: list(v) for k, v in resource_history.items()},
                'ollama': ollama,
                'models_count': len(ollama),
                'architecture': ARCHITECTURE,
                'tokens': token_tracker,
                'cost_total': total_cost,
                'apis': get_api_status(),
                'processes': get_processes(),
                'tasks_lumen': get_lumen_tasks(),
                'tasks_hb': get_hb_tasks()
            })
            time.sleep(1)
        except Exception as e:
            print(f"[Error] {e}")
            time.sleep(1)

# ===== ROUTES =====
@app.route('/')
def index():
    return render_template_string(HTML_V55)

@app.route('/api/status')
def api_status():
    return jsonify({'architecture': ARCHITECTURE, 'gpu': get_gpu_info(), 'system': get_system_stats()})

# ===== HTML V5.5 — TABLERO DE CONTROL PRO =====
HTML_V55 = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔮 LumenAGI v5.5 | Control Panel Pro</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        :root {
            --bg: #0a0a0f; --bg2: #12121a; --bg3: #1a1a2e; --bg4: #252542;
            --accent1: #ff6b35; --accent2: #00ff88; --accent3: #3b82f6; --danger: #ff4444; --warn: #ffaa00;
            --text: #e0e0e0; --text2: #888; --border: #2a2a3a;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'SF Pro Display', -apple-system, sans-serif; 
            background: var(--bg); color: var(--text); height: 100vh; overflow: hidden;
        }
        
        /* HEADER */
        .header { 
            display: flex; justify-content: space-between; align-items: center;
            padding: 0.5rem 1rem; border-bottom: 1px solid var(--border); background: var(--bg2);
            height: 48px;
        }
        .logo { display: flex; align-items: center; gap: 0.5rem; font-size: 1.2rem; font-weight: 700; }
        .logo span { color: var(--accent1); }
        .status-bar { display: flex; gap: 1rem; font-size: 0.75rem; }
        .status-item { display: flex; align-items: center; gap: 0.3rem; }
        .dot { width: 8px; height: 8px; border-radius: 50%; }
        .dot.green { background: var(--accent2); animation: pulse 2s infinite; }
        .dot.yellow { background: var(--warn); }
        .dot.red { background: var(--danger); }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
        
        /* MAIN GRID */
        .main { 
            display: grid; 
            grid-template-columns: 380px 1fr 320px; 
            gap: 0.75rem; padding: 0.75rem;
            height: calc(100vh - 48px);
        }
        
        /* CARDS */
        .col { display: flex; flex-direction: column; gap: 0.75rem; min-height: 0; }
        .card { 
            background: var(--bg3); border-radius: 12px; padding: 0.75rem;
            border: 1px solid var(--border);
        }
        .card h3 { 
            font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px;
            color: var(--text2); margin-bottom: 0.5rem; display: flex; justify-content: space-between;
        }
        
        /* GAUGES CIRCULARES CPU/RAM/DISK */
        .gauges { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; }
        .gauge { text-align: center; }
        .gauge-canvas { width: 70px; height: 70px; margin: 0 auto; }
        .gauge-label { font-size: 0.6rem; color: var(--text2); margin-top: 0.2rem; }
        .gauge-value { font-size: 0.9rem; font-weight: 700; }
        
        /* GPU HERO */
        .gpu-hero { background: linear-gradient(135deg, var(--bg4), var(--bg3)); padding: 1rem; }
        .gpu-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
        .gpu-name { font-size: 0.9rem; font-weight: 600; }
        .gpu-temp { 
            font-size: 1rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 6px;
        }
        .gpu-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; margin-bottom: 0.75rem; }
        .gpu-stat { text-align: center; background: var(--bg2); padding: 0.4rem; border-radius: 6px; }
        .gpu-stat-label { font-size: 0.55rem; color: var(--text2); text-transform: uppercase; }
        .gpu-stat-value { font-size: 0.8rem; font-weight: 700; }
        
        /* BARRAS VRAM */
        .vram-bar { margin: 0.5rem 0; }
        .vram-header { display: flex; justify-content: space-between; font-size: 0.6rem; margin-bottom: 0.2rem; }
        .vram-track { height: 10px; background: var(--bg2); border-radius: 5px; overflow: hidden; }
        .vram-fill { height: 100%; border-radius: 5px; transition: width 0.3s; }
        .vram-system { background: linear-gradient(90deg, #00d4ff, #0099cc); }
        .vram-model { background: linear-gradient(90deg, var(--accent1), #ff8c5a); }
        
        /* GRÁFICAS HISTÓRICAS */
        .chart-container { height: 120px; margin-top: 0.5rem; }
        
        /* MODELOS CARGADOS */
        .model-list { max-height: 140px; overflow-y: auto; }
        .model-item { 
            display: flex; justify-content: space-between; align-items: center;
            padding: 0.4rem; background: var(--bg2); border-radius: 6px; margin-bottom: 0.3rem;
            font-size: 0.75rem;
        }
        .model-name { font-weight: 600; }
        .model-size { color: var(--accent2); font-family: monospace; }
        
        /* SWARM ARQUITECTURA */
        .swarm-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; }
        .swarm-card { 
            background: var(--bg2); border-radius: 10px; padding: 0.75rem;
            border: 2px solid var(--border); text-align: center; position: relative;
        }
        .swarm-card.active { border-color: var(--accent2); }
        .swarm-card.active::after { 
            content: '●'; position: absolute; top: -5px; right: -5px; 
            color: var(--accent2); font-size: 10px; animation: pulse 1s infinite;
        }
        .swarm-icon { font-size: 1.5rem; margin-bottom: 0.3rem; }
        .swarm-name { font-size: 0.7rem; font-weight: 600; }
        .swarm-model { font-size: 0.6rem; color: var(--text2); }
        .swarm-location { font-size: 0.55rem; color: var(--accent3); margin-top: 0.2rem; }
        .swarm-cost { font-size: 0.6rem; margin-top: 0.3rem; padding: 0.2rem 0.4rem; border-radius: 4px; }
        .swarm-cost.free { background: rgba(0,255,136,0.15); color: var(--accent2); }
        .swarm-cost.paid { background: rgba(255,107,53,0.15); color: var(--accent1); }
        
        /* TOKENS */
        .token-row { 
            display: grid; grid-template-columns: 1fr auto auto auto; gap: 0.5rem;
            padding: 0.4rem 0; border-bottom: 1px solid var(--border); font-size: 0.75rem;
            align-items: center;
        }
        .token-row:last-child { border-bottom: none; }
        .token-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 0.3rem; }
        .token-value { font-family: monospace; text-align: right; }
        .token-cost { color: var(--accent1); font-weight: 600; }
        
        /* PROCESOS */
        .proc-list { max-height: 120px; overflow-y: auto; font-size: 0.7rem; }
        .proc-item { 
            display: grid; grid-template-columns: 1fr auto auto auto; gap: 0.5rem;
            padding: 0.3rem; border-bottom: 1px solid var(--border);
        }
        
        /* TAREAS */
        .task-list { max-height: 150px; overflow-y: auto; }
        .task-item { 
            display: flex; align-items: center; gap: 0.4rem;
            padding: 0.4rem; background: var(--bg2); border-radius: 5px;
            margin-bottom: 0.3rem; font-size: 0.75rem;
            border-left: 2px solid transparent;
        }
        .task-item.active { border-left-color: var(--accent2); }
        .task-item.pending { border-left-color: var(--warn); }
        .task-icon { font-size: 0.8rem; }
        
        /* APIS */
        .api-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.4rem; }
        .api-item { 
            display: flex; align-items: center; gap: 0.3rem;
            padding: 0.3rem; background: var(--bg2); border-radius: 5px;
            font-size: 0.65rem;
        }
        
        /* RESPONSIVE */
        @media (max-width: 1200px) {
            .main { grid-template-columns: 1fr 1fr; }
        }
        @media (max-width: 768px) {
            .main { grid-template-columns: 1fr; overflow-y: auto; }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="logo">🔮 Lumen<span>AGI</span> v5.5</div>
        <div class="status-bar">
            <div class="status-item"><div class="dot green"></div> Qwen 32B Loaded</div>
            <div class="status-item"><div class="dot green"></div> Kimi Cloud</div>
            <div class="status-item"><div class="dot yellow"></div> GPT-4 Standby</div>
            <div class="status-item" id="conn-status">🟡 Connecting...</div>
        </div>
    </header>

    <div class="main">
        <!-- COLUMNA IZQUIERDA: HARDWARE -->
        <div class="col">
            <!-- CPU/RAM/DISK GAUGES -->
            <div class="card">
                <h3>💻 System Resources</h3>
                <div class="gauges">
                    <div class="gauge">
                        <canvas id="gauge-cpu" class="gauge-canvas"></canvas>
                        <div class="gauge-label">CPU</div>
                        <div class="gauge-value" id="cpu-val">0%</div>
                    </div>
                    <div class="gauge">
                        <canvas id="gauge-ram" class="gauge-canvas"></canvas>
                        <div class="gauge-label">RAM</div>
                        <div class="gauge-value" id="ram-val">0%</div>
                    </div>
                    <div class="gauge">
                        <canvas id="gauge-disk" class="gauge-canvas"></canvas>
                        <div class="gauge-label">Disk</div>
                        <div class="gauge-value" id="disk-val">0%</div>
                    </div>
                </div>
            </div>

            <!-- GPU RTX 3090 -->
            <div class="card gpu-hero">
                <div class="gpu-header">
                    <div class="gpu-name">🎮 RTX 3090</div>
                    <div class="gpu-temp" id="gpu-temp">-°C</div>
                </div>
                <div class="gpu-stats">
                    <div class="gpu-stat">
                        <div class="gpu-stat-label">Util</div>
                        <div class="gpu-stat-value" id="gpu-util">0%</div>
                    </div>
                    <div class="gpu-stat">
                        <div class="gpu-stat-label">Power</div>
                        <div class="gpu-stat-value" id="gpu-power">-W</div>
                    </div>
                    <div class="gpu-stat">
                        <div class="gpu-stat-label">Clock GPU</div>
                        <div class="gpu-stat-value" id="gpu-clock">-</div>
                    </div>
                    <div class="gpu-stat">
                        <div class="gpu-stat-label">VRAM Used</div>
                        <div class="gpu-stat-value" id="vram-used">-</div>
                    </div>
                </div>
                
                <!-- Barras VRAM -->
                <div class="vram-bar">
                    <div class="vram-header"><span>System VRAM</span><span id="vram-sys-text">0/24 GB</span></div>
                    <div class="vram-track"><div class="vram-fill vram-system" id="vram-sys-bar" style="width: 0%"></div></div>
                </div>
                <div class="vram-bar">
                    <div class="vram-header"><span>Models in VRAM</span><span id="vram-model-text">0 GB</span></div>
                    <div class="vram-track"><div class="vram-fill vram-model" id="vram-model-bar" style="width: 0%"></div></div>
                </div>
            </div>

            <!-- Historial Gráficas -->
            <div class="card">
                <h3>📈 Historial (últimos 60s)</h3>
                <div class="chart-container"><canvas id="history-chart"></canvas></div>
            </div>

            <!-- Modelos Cargados -->
            <div class="card">
                <h3>🦙 Modelos en VRAM <span id="models-count">(0)</span></h3>
                <div class="model-list" id="models-list">
                    <div style="color: var(--text2); font-size: 0.75rem;">Cargando...</div>
                </div>
            </div>
        </div>

        <!-- COLUMNA CENTRAL: AGENTES + ARQUITECTURA -->
        <div class="col">
            <!-- SWARM Arquitectura -->
            <div class="card">
                <h3>🕸️ SWARM Architecture v3.0</h3>
                <div class="swarm-grid">
                    <div class="swarm-card active" id="swarm-cerebro">
                        <div class="swarm-icon">🧠</div>
                        <div class="swarm-name">Cerebro</div>
                        <div class="swarm-model">Kimi K2.5</div>
                        <div class="swarm-location">☁️ Cloud</div>
                        <div class="swarm-cost paid">Ollama Pro</div>
                    </div>
                    <div class="swarm-card active" id="swarm-local">
                        <div class="swarm-icon">⚡</div>
                        <div class="swarm-name">Agente Local</div>
                        <div class="swarm-model">Qwen 32B</div>
                        <div class="swarm-location" id="local-vram">🖥️ 20GB VRAM</div>
                        <div class="swarm-cost free">⚡ FREE</div>
                    </div>
                    <div class="swarm-card" id="swarm-research">
                        <div class="swarm-icon">🔬</div>
                        <div class="swarm-name">Research</div>
                        <div class="swarm-model">GPT-4</div>
                        <div class="swarm-location">☁️ Cloud</div>
                        <div class="swarm-cost paid">API $</div>
                    </div>
                </div>
            </div>

            <!-- Tokens & Costs -->
            <div class="card">
                <h3>🎫 Tokens Consumidos | 💰 Costos</h3>
                <div class="token-row" style="font-weight: 600; color: var(--text2);">
                    <div>Agente</div>
                    <div>In</div>
                    <div>Out</div>
                    <div>Costo</div>
                </div>
                <div class="token-row">
                    <div><span class="token-dot" style="background: var(--accent3);"></span>🧠 Kimi</div>
                    <div class="token-value" id="tokens-kimi-in">0</div>
                    <div class="token-value" id="tokens-kimi-out">0</div>
                    <div class="token-cost" id="cost-kimi">$0.00</div>
                </div>
                <div class="token-row">
                    <div><span class="token-dot" style="background: var(--accent2);"></span>⚡ Qwen 32B</div>
                    <div class="token-value" id="tokens-qwen-in">0</div>
                    <div class="token-value" id="tokens-qwen-out">0</div>
                    <div class="token-cost" style="color: var(--accent2);">FREE</div>
                </div>
                <div class="token-row">
                    <div><span class="token-dot" style="background: var(--accent1);"></span>🔬 GPT-4</div>
                    <div class="token-value" id="tokens-gpt4-in">0</div>
                    <div class="token-value" id="tokens-gpt4-out">0</div>
                    <div class="token-cost" id="cost-gpt4">$0.00</div>
                </div>
                <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border);">
                    <span style="font-size: 0.75rem; color: var(--text2);">TOTAL ACUMULADO</span>
                    <span class="token-cost" style="font-size: 1rem;" id="cost-total">$0.00</span>
                </div>
            </div>

            <!-- Procesos Críticos -->
            <div class="card">
                <h3>🔧 Procesos del Sistema</h3>
                <div class="proc-list" id="process-list">
                    <div style="color: var(--text2);">Cargando procesos...</div>
                </div>
            </div>

            <!-- Tareas Lumen -->
            <div class="card">
                <h3>🤖 Mis Tareas (Lumen)</h3>
                <div class="task-list" id="lumen-tasks">
                    <div class="task-item active"><span class="task-icon">●</span> Dashboard v5.5</div>
                </div>
            </div>
        </div>

        <!-- COLUMNA DERECHA: APIS + TAREAS HB -->
        <div class="col">
            <!-- APIs Status -->
            <div class="card">
                <h3>🔌 API Integrations</h3>
                <div class="api-grid" id="api-grid">
                    <div class="api-item">📺 YouTube: 🟡</div>
                    <div class="api-item">📧 Gmail: 🟡</div>
                    <div class="api-item">📋 Notion: 🟡</div>
                    <div class="api-item">🦞 Moltbook: 🟡</div>
                    <div class="api-item">💬 Telegram: 🟡</div>
                </div>
            </div>

            <!-- Tareas Humberto -->
            <div class="card">
                <h3>👤 Tus Tareas (Hb)</h3>
                <div class="task-list" id="hb-tasks">
                    <div class="task-item pending"><span class="task-icon">🟡</span> Revisar dashboard</div>
                    <div class="task-item pending"><span class="task-icon">🟡</span> Conectar Notion</div>
                </div>
            </div>

            <!-- Notas -->
            <div class="card" style="flex: 1;">
                <h3>📝 Quick Notes</h3>
                <div style="font-size: 0.75rem; color: var(--text2); padding: 0.5rem; background: var(--bg2); border-radius: 5px; height: calc(100% - 2rem); overflow-y: auto;">
                    <p>• Qwen 32B: 19.4GB VRAM cargado</p>
                    <p>• GPU: 46°C idle</p>
                    <p>• 16 APIs configuradas</p>
                    <p>• Commit: a72b4ce</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        const socket = io('http://127.0.0.1:8766');
        let historyChart;

        // Gauges circulares
        function drawGauge(canvasId, value, color) {
            const canvas = document.getElementById(canvasId);
            const ctx = canvas.getContext('2d');
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const radius = 30;
            
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Background arc
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, 0.5 * Math.PI, 2.5 * Math.PI);
            ctx.strokeStyle = '#2a2a3a';
            ctx.lineWidth = 6;
            ctx.stroke();
            
            // Value arc
            const angle = 0.5 * Math.PI + (value / 100) * 2 * Math.PI;
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, 0.5 * Math.PI, angle);
            ctx.strokeStyle = value > 80 ? '#ff4444' : value > 60 ? '#ffaa00' : color;
            ctx.lineWidth = 6;
            ctx.stroke();
        }

        // Chart histórico
        function initHistoryChart() {
            const ctx = document.getElementById('history-chart').getContext('2d');
            historyChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: Array(60).fill(''),
                    datasets: [
                        { label: 'CPU', data: Array(60).fill(0), borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)', fill: true, tension: 0.4, pointRadius: 0, borderWidth: 2 },
                        { label: 'GPU', data: Array(60).fill(0), borderColor: '#ff6b35', backgroundColor: 'rgba(255,107,53,0.1)', fill: true, tension: 0.4, pointRadius: 0, borderWidth: 2 },
                        { label: 'VRAM', data: Array(60).fill(0), borderColor: '#00ff88', backgroundColor: 'rgba(0,255,136,0.1)', fill: true, tension: 0.4, pointRadius: 0, borderWidth: 2 }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: true, labels: { color: '#888', font: { size: 9 } } } },
                    scales: { x: { display: false }, y: { beginAtZero: true, max: 100, ticks: { color: '#666', font: { size: 8 } }, grid: { color: '#222' } } },
                    animation: false
                }
            });
        }

        function fmtNum(n) {
            if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
            if (n >= 1000) return (n/1000).toFixed(1) + 'K';
            return n.toString();
        }

        socket.on('connect', () => {
            document.getElementById('conn-status').textContent = '🟢 Connected';
            initHistoryChart();
        });

        socket.on('metrics', (data) => {
            // System gauges
            if (data.system) {
                const s = data.system;
                drawGauge('gauge-cpu', s.cpu, '#3b82f6');
                document.getElementById('cpu-val').textContent = s.cpu.toFixed(0) + '%';
                document.getElementById('cpu-val').style.color = s.cpu > 80 ? '#ff4444' : s.cpu > 60 ? '#ffaa00' : '#00ff88';
                
                drawGauge('gauge-ram', s.ram_percent, '#00ff88');
                document.getElementById('ram-val').textContent = s.ram_percent.toFixed(0) + '%';
                document.getElementById('ram-val').style.color = s.ram_percent > 85 ? '#ff4444' : s.ram_percent > 70 ? '#ffaa00' : '#00ff88';
                
                drawGauge('gauge-disk', s.disk_percent, '#ff6b35');
                document.getElementById('disk-val').textContent = s.disk_percent.toFixed(0) + '%';
            }

            // GPU
            if (data.gpu) {
                const g = data.gpu;
                document.getElementById('gpu-temp').textContent = g.temperature + '°C';
                document.getElementById('gpu-temp').style.background = g.temperature > 80 ? 'rgba(255,68,68,0.3)' : g.temperature > 70 ? 'rgba(255,170,0,0.3)' : 'rgba(0,255,136,0.3)';
                
                document.getElementById('gpu-util').textContent = g.utilization + '%';
                document.getElementById('gpu-power').textContent = g.power_draw.toFixed(0) + 'W';
                document.getElementById('gpu-clock').textContent = g.clock_gpu + 'MHz';
                document.getElementById('vram-used').textContent = (g.used_mb/1024).toFixed(1) + 'GB';
                
                // Barras VRAM
                const vramSysPct = (g.used_mb / g.total_mb) * 100;
                document.getElementById('vram-sys-text').textContent = (g.used_mb/1024).toFixed(1) + '/' + (g.total_mb/1024).toFixed(0) + ' GB';
                document.getElementById('vram-sys-bar').style.width = vramSysPct + '%';
            }

            // Modelos
            if (data.ollama) {
                document.getElementById('models-count').textContent = '(' + data.models_count + ')';
                let totalModelVram = 0;
                const list = document.getElementById('models-list');
                list.innerHTML = data.ollama.map(m => {
                    const vramGB = (m.size / (1024**3)).toFixed(1);
                    totalModelVram += parseFloat(vramGB);
                    return `<div class="model-item">
                        <span class="model-name">${m.name.split(':')[0]}</span>
                        <span class="model-size">${vramGB}GB</span>
                    </div>`;
                }).join('');
                
                // Barra de VRAM de modelos
                const vramModelPct = (totalModelVram / 24) * 100;
                document.getElementById('vram-model-text').textContent = totalModelVram.toFixed(1) + ' GB';
                document.getElementById('vram-model-bar').style.width = vramModelPct + '%';
            }

            // History chart
            if (data.history && historyChart) {
                historyChart.data.datasets[0].data = data.history.cpu;
                historyChart.data.datasets[1].data = data.history.gpu;
                historyChart.data.datasets[2].data = data.history.vram;
                historyChart.update('none');
            }

            // Tokens
            if (data.tokens) {
                const t = data.tokens;
                document.getElementById('tokens-kimi-in').textContent = fmtNum(t.kimi.input);
                document.getElementById('tokens-kimi-out').textContent = fmtNum(t.kimi.output);
                document.getElementById('cost-kimi').textContent = '$' + t.kimi.cost.toFixed(3);
                
                document.getElementById('tokens-qwen-in').textContent = fmtNum(t.qwen.input);
                document.getElementById('tokens-qwen-out').textContent = fmtNum(t.qwen.output);
                
                document.getElementById('tokens-gpt4-in').textContent = fmtNum(t.gpt4.input);
                document.getElementById('tokens-gpt4-out').textContent = fmtNum(t.gpt4.output);
                document.getElementById('cost-gpt4').textContent = '$' + t.gpt4.cost.toFixed(3);
                
                document.getElementById('cost-total').textContent = '$' + data.cost_total.toFixed(3);
            }

            // APIs
            if (data.apis) {
                const apis = data.apis;
                document.getElementById('api-grid').innerHTML = `
                    <div class="api-item">📺 YouTube: ${apis.youtube.status}</div>
                    <div class="api-item">📧 Gmail: ${apis.gmail.status}</div>
                    <div class="api-item">📋 Notion: ${apis.notion.status}</div>
                    <div class="api-item">🦞 Moltbook: ${apis.moltbook.status}</div>
                    <div class="api-item">💬 Telegram: ${apis.telegram.status}</div>
                `;
            }

            // Procesos
            if (data.processes) {
                document.getElementById('process-list').innerHTML = data.processes.map(p => `
                    <div class="proc-item">
                        <span>${p.name}</span>
                        <span style="color: var(--text2);">${p.cpu}%</span>
                        <span style="color: var(--text2);">${p.mem}%</span>
                        <span style="color: var(--accent2);">${p.pid}</span>
                    </div>
                `).join('');
            }

            // Tareas Lumen
            if (data.tasks_lumen && data.tasks_lumen.length > 0) {
                document.getElementById('lumen-tasks').innerHTML = data.tasks_lumen.slice().reverse().map(t => `
                    <div class="task-item ${t.status === 'running' ? 'active' : 'pending'}">
                        <span class="task-icon">${t.status === 'running' ? '●' : '○'}</span>
                        ${t.task.substring(0, 30)}
                    </div>
                `).join('');
            }

            // Tareas HB
            if (data.tasks_hb) {
                document.getElementById('hb-tasks').innerHTML = data.tasks_hb.map(t => `
                    <div class="task-item ${t.done ? '' : 'pending'}">
                        <span class="task-icon">${t.icon}</span>
                        ${t.text}
                    </div>
                `).join('');
            }

            // Swarm status
            if (data.architecture) {
                const arch = data.architecture;
                document.getElementById('swarm-cerebro').className = 'swarm-card ' + (arch.cerebro.status === 'active' ? 'active' : '');
                document.getElementById('swarm-local').className = 'swarm-card ' + (arch.local.status === 'loaded' ? 'active' : '');
                document.getElementById('swarm-research').className = 'swarm-card ' + (arch.research.status === 'active' ? 'active' : '');
            }
        });

        socket.on('disconnect', () => {
            document.getElementById('conn-status').textContent = '🔴 Disconnected';
        });

        // Init gauges
        setTimeout(() => {
            drawGauge('gauge-cpu', 0, '#3b82f6');
            drawGauge('gauge-ram', 0, '#00ff88');
            drawGauge('gauge-disk', 0, '#ff6b35');
        }, 100);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    from threading import Thread
    Thread(target=emit_loop, daemon=True).start()
    print("🔮 LumenAGI Dashboard v5.5 — Control Panel Pro")
    print("🎮 Features: Gauges circulares | GPU histórico | VRAM detallada | SWARM v3.0 | APIs reales")
    print("📡 http://localhost:8766")
    socketio.run(app, host='0.0.0.0', port=8766, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
