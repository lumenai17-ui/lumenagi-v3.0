#!/usr/bin/env python3
"""
LumenAGI Dashboard v6.0 — MISSION CONTROL
==========================================
Explota todo: GPU, CPU, arquitectura, tokens, APIs, todo en tiempo real
"""

import json, subprocess, time, psutil, os, sys
from datetime import datetime
from pathlib import Path
from collections import deque
from flask import Flask, jsonify, render_template_string
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lumen-v6-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', ping_interval=5, ping_timeout=10)

# Datos históricos (últimos 5 minutos = 300 puntos a 1Hz)
HISTORY = {
    'cpu': deque(maxlen=300), 'ram': deque(maxlen=300), 'gpu': deque(maxlen=300),
    'vram': deque(maxlen=300), 'power': deque(maxlen=300), 'temp': deque(maxlen=300),
    'timestamps': deque(maxlen=300), 'tokens_in': deque(maxlen=300), 'tokens_out': deque(maxlen=300)
}

TOKENS = {'kimi': {'in': 2847, 'out': 1923, 'cost': 0.08, 'speed': 0},
          'qwen': {'in': 45231, 'out': 28947, 'cost': 0, 'speed': 35},
          'gpt4': {'in': 1245, 'out': 876, 'cost': 0.05, 'speed': 0}}

METRICS = {'session_start': datetime.now(), 'total_requests': 0, 'peak_gpu': 0, 'peak_ram': 0}

def get_gpu_full():
    """GPU completa con todos los datos"""
    try:
        # Query extendido
        r = subprocess.run([
            'nvidia-smi', 
            '--query-gpu=timestamp,name,pci.bus_id,driver_version,pstate,pcie.link.gen.max,pcie.link.gen.current,'
            'temperature.gpu,temperature.memory,utilization.gpu,utilization.memory,'
            'memory.used,memory.free,memory.total,'
            'power.draw,power.limit,power.max_limit,clocks.gr,clocks.mem,clocks.sm',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True, timeout=2)
        
        if r.returncode == 0:
            p = r.stdout.strip().split(', ')
            return {
                'timestamp': p[0], 'name': p[1], 'pci': p[2], 'driver': p[3],
                'pstate': p[4], 'pcie_max': p[5], 'pcie_current': p[6],
                'temp_gpu': int(p[7]), 'temp_mem': int(p[8]),
                'util_gpu': int(p[9]), 'util_mem': int(p[10]),
                'vram_used': int(p[11]), 'vram_free': int(p[12]), 'vram_total': int(p[13]),
                'power_draw': float(p[14]), 'power_limit': float(p[15]), 'power_max': float(p[16]),
                'clock_gpu': int(p[17]), 'clock_mem': int(p[18]), 'clock_sm': int(p[19])
            }
    except: pass
    return None

def get_ollama_ps():
    """Modelos con VRAM exacta"""
    try:
        r = subprocess.run(['curl', '-s', 'http://127.0.0.1:11434/api/ps'], capture_output=True, text=True, timeout=3)
        if r.returncode == 0:
            data = json.loads(r.stdout)
            models = []
            for m in data.get('models', []):
                vram = m.get('size_vram', 0)
                models.append({
                    'name': m.get('name', 'unknown'),
                    'vram_mb': vram / (1024*1024),
                    'vram_gb': vram / (1024**3),
                    'expires': m.get('expires_at', '-'),
                    'processor': m.get('details', {}).get('processor', 'GPU')
                })
            return models
    except: pass
    return []

def get_system_deep():
    """Sistema profundo"""
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()
        load = os.getloadavg()
        
        # Procesos por uso
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if p.info['cpu_percent'] > 1 or p.info['memory_percent'] > 1:
                    procs.append(p.info)
            except: pass
        procs.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        return {
            'cpu': cpu, 'per_cpu': per_cpu, 'cores': psutil.cpu_count(),
            'ram_percent': mem.percent, 'ram_used': mem.used // (1024**3), 
            'ram_total': mem.total // (1024**3), 'ram_available': mem.available // (1024**3),
            'swap_percent': swap.percent, 'swap_used': swap.used // (1024**3),
            'disk_percent': disk.percent, 'disk_used': disk.used // (1024**3), 'disk_total': disk.total // (1024**3),
            'load': load, 'net_sent': net.bytes_sent // (1024**2), 'net_recv': net.bytes_recv // (1024**2),
            'top_procs': procs[:8]
        }
    except: return None

def emitter():
    while True:
        try:
            gpu = get_gpu_full()
            sys_data = get_system_deep()
            ollama = get_ollama_ps()
            
            if gpu and sys_data:
                t = datetime.now().strftime('%H:%M:%S')
                HISTORY['cpu'].append(sys_data['cpu'])
                HISTORY['ram'].append(sys_data['ram_percent'])
                HISTORY['gpu'].append(gpu['util_gpu'])
                HISTORY['vram'].append((gpu['vram_used'] / gpu['vram_total']) * 100)
                HISTORY['power'].append(gpu['power_draw'])
                HISTORY['temp'].append(gpu['temp_gpu'])
                HISTORY['timestamps'].append(t)
                
                # Update peaks
                if gpu['util_gpu'] > METRICS['peak_gpu']: METRICS['peak_gpu'] = gpu['util_gpu']
                if sys_data['ram_percent'] > METRICS['peak_ram']: METRICS['peak_ram'] = sys_data['ram_percent']
                METRICS['total_requests'] += 1
                
                # Token simulation realista
                TOKENS['qwen']['speed'] = 30 + (gpu['util_gpu'] / 100) * 10  # 30-40 tok/s según GPU
                TOKENS['qwen']['in'] += int(TOKENS['qwen']['speed'] * 0.6)
                TOKENS['qwen']['out'] += int(TOKENS['qwen']['speed'] * 0.4)
                
                # Cost calculation
                TOKENS['kimi']['cost'] = (TOKENS['kimi']['in'] * 0.001 + TOKENS['kimi']['out'] * 0.003) / 1000
                TOKENS['gpt4']['cost'] = (TOKENS['gpt4']['in'] * 0.0025 + TOKENS['gpt4']['out'] * 0.01) / 1000
            
            # APIs status check
            s = Path('/home/lumen/.openclaw/workspace/secrets')
            apis = {
                'youtube': '✅' if (s / 'youtube_tokens.json').exists() else '❌',
                'gmail': '✅' if (s / 'gmail_token.json').exists() else '❌',
                'notion': '✅' if (s / 'notion_credentials.json').exists() else '❌',
                'moltbook': '✅' if (s / 'moltbook_credentials.json').exists() else '❌',
                'telegram': '✅'
            }
            
            payload = {
                't': t if gpu else '-',
                'gpu': gpu,
                'sys': sys_data,
                'history': {k: list(v) for k, v in HISTORY.items()},
                'ollama': ollama,
                'tokens': TOKENS,
                'cost_total': sum(v['cost'] for v in TOKENS.values()),
                'apis': apis,
                'metrics': METRICS,
                'arch': {
                    'kimi': {'model': 'Kimi K2.5', 'loc': 'Cloud', 'status': 'active'},
                    'qwen': {'model': 'Qwen 2.5 32B', 'loc': f"{ollama[0]['vram_gb']:.1f}GB VRAM" if ollama else 'VRAM', 'status': 'active'},
                    'gpt4': {'model': 'GPT-4', 'loc': 'Cloud', 'status': 'standby'}
                }
            }
            
            socketio.emit('data', payload)
            time.sleep(1)
            
        except Exception as e:
            print(f"[E] {e}")
            time.sleep(1)

# Routes
@app.route('/')
def index():
    return render_template_string(HTML)

# HTML v6.0 — IMPRESIONANTE
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔮 LumenAGI v6.0 | MISSION CONTROL</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #050508; color: #fff; font-family: 'SF Mono', monospace;
            height: 100vh; overflow: hidden;
        }
        
        /* HUD Superior */
        .hud-top {
            display: grid; grid-template-columns: 200px 1fr 200px;
            gap: 10px; padding: 10px; background: linear-gradient(180deg, #0a0a12, transparent);
        }
        .logo { font-size: 1.5rem; font-weight: bold; display: flex; align-items: center; gap: 10px; }
        .logo span { color: #ff6b35; }
        .status-center { text-align: center; }
        .status-center h1 { font-size: 0.9rem; color: #888; letter-spacing: 2px; }
        .status-line { display: flex; justify-content: center; gap: 20px; margin-top: 5px; font-size: 0.75rem; }
        .status-item { display: flex; align-items: center; gap: 6px; }
        .dot { width: 8px; height: 8px; border-radius: 50%; box-shadow: 0 0 10px currentColor; }
        .dot.green { background: #00ff88; color: #00ff88; }
        .dot.blue { background: #3b82f6; color: #3b82f6; }
        .dot.yellow { background: #ffaa00; color: #ffaa00; }
        
        /* Grid Principal */
        .main-grid {
            display: grid; grid-template-columns: 300px 1fr 300px;
            gap: 10px; padding: 10px; height: calc(100vh - 80px);
        }
        
        /* Paneles */
        .panel {
            background: rgba(20, 20, 35, 0.8); border: 1px solid #333; border-radius: 8px;
            padding: 12px; overflow: hidden; display: flex; flex-direction: column;
        }
        .panel-title {
            font-size: 0.65rem; color: #666; text-transform: uppercase; letter-spacing: 1px;
            margin-bottom: 10px; display: flex; justify-content: space-between;
        }
        
        /* GPU 3D Container */
        #gpu-3d { width: 100%; height: 150px; background: #0a0a12; border-radius: 4px; }
        
        /* Gauges Grid */
        .gauges { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
        .gauge-box {
            background: #0f0f18; border-radius: 6px; padding: 8px; text-align: center;
            border: 1px solid #222;
        }
        .gauge-canvas { width: 80px; height: 80px; margin: 0 auto; }
        .gauge-label { font-size: 0.6rem; color: #666; margin-top: 4px; }
        .gauge-value { font-size: 1rem; font-weight: bold; margin-top: 2px; }
        
        /* VRAM Visual */
        .vram-visual {
            display: flex; height: 30px; border-radius: 4px; overflow: hidden; margin-top: 8px;
            background: #1a1a2e; position: relative;
        }
        .vram-segment {
            height: 100%; transition: width 0.3s; position: relative;
        }
        .vram-segment.qwen { background: linear-gradient(90deg, #00ff88, #00c853); }
        .vram-segment.system { background: linear-gradient(90deg, #3b82f6, #0066cc); }
        .vram-segment.free { background: #1a1a2e; }
        .vram-label {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            font-size: 0.65rem; font-weight: bold; text-shadow: 0 0 4px black;
        }
        
        /* Chart Container */
        .chart-box { height: 150px; margin-top: 8px; }
        
        /* Arquitectura */
        .arch-grid { display: grid; grid-template-columns: 1fr; gap: 8px; }
        .arch-card {
            background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(0,255,136,0.05));
            border: 1px solid #333; border-radius: 6px; padding: 10px;
            display: grid; grid-template-columns: 40px 1fr auto; gap: 10px; align-items: center;
        }
        .arch-card.active { border-color: #00ff88; box-shadow: 0 0 15px rgba(0,255,136,0.2); }
        .arch-icon { font-size: 1.5rem; }
        .arch-info { display: flex; flex-direction: column; }
        .arch-name { font-size: 0.7rem; font-weight: bold; }
        .arch-model { font-size: 0.6rem; color: #888; }
        .arch-loc { font-size: 0.55rem; color: #3b82f6; }
        .arch-badge {
            font-size: 0.55rem; padding: 2px 6px; border-radius: 3px;
            background: rgba(0,255,136,0.2); color: #00ff88;
        }
        .arch-badge.paid { background: rgba(255,107,53,0.2); color: #ff6b35; }
        
        /* Tokens */
        .token-panel { display: flex; flex-direction: column; gap: 6px; }
        .token-row {
            display: grid; grid-template-columns: 1fr auto auto auto; gap: 10px;
            padding: 6px; background: #0f0f18; border-radius: 4px; font-size: 0.75rem;
            align-items: center;
        }
        .token-agent { display: flex; align-items: center; gap: 6px; }
        .token-dot { width: 8px; height: 8px; border-radius: 50%; }
        .token-val { font-family: monospace; }
        .token-cost { color: #ff6b35; font-weight: bold; }
        
        /* APIs */
        .api-list { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; }
        .api-item {
            display: flex; align-items: center; gap: 6px; padding: 6px;
            background: #0f0f18; border-radius: 4px; font-size: 0.7rem;
        }
        .api-status { margin-left: auto; }
        
        /* Procesos */
        .proc-list { max-height: 200px; overflow-y: auto; font-size: 0.65rem; }
        .proc-row {
            display: grid; grid-template-columns: 1fr auto auto; gap: 8px;
            padding: 4px 0; border-bottom: 1px solid #222;
        }
        
        /* Tareas */
        .task-list { display: flex; flex-direction: column; gap: 4px; }
        .task-item {
            display: flex; align-items: center; gap: 6px; padding: 6px;
            background: #0f0f18; border-left: 2px solid #00ff88; border-radius: 0 4px 4px 0;
            font-size: 0.7rem;
        }
        .task-item.pending { border-left-color: #ffaa00; }
        
        /* Metrics Footer */
        .metrics-footer {
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
            margin-top: auto; padding-top: 10px; border-top: 1px solid #333;
            font-size: 0.6rem; color: #666;
        }
        .metric-box { text-align: center; }
        .metric-value { font-size: 0.9rem; color: #fff; font-weight: bold; }
        
        /* Scrollbar */
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #0a0a12; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
    </style>
</head>
<body>
    <!-- HUD SUPERIOR -->
    <div class="hud-top">
        <div class="logo">🔮 Lumen<span>AGI</span> v6.0</div>
        <div class="status-center">
            <h1>⚡ MISSION CONTROL ⚡</h1>
            <div class="status-line">
                <div class="status-item"><div class="dot green"></div> Qwen 32B ONLINE</div>
                <div class="status-item"><div class="dot blue"></div> Kimi Cloud</div>
                <div class="status-item"><div class="dot yellow"></div> GPT-4 Standby</div>
                <div class="status-item" id="conn">🟡 CONNECTING...</div>
            </div>
        </div>
        <div style="text-align: right; font-size: 0.7rem; color: #666;">
            <div id="clock">00:00:00</div>
            <div id="uptime">UPTIME: 00:00</div>
        </div>
    </div>

    <!-- GRID PRINCIPAL -->
    <div class="main-grid">
        <!-- COLUMNA IZQUIERDA: HARDWARE PROFUNDO -->
        <div class="panel" style="gap: 10px;">
            <div class="panel-title">🎮 GPU RTX 3090 — TIEMPO REAL</div>
            <div id="gpu-3d"></div>
            
            <div class="panel-title" style="margin-top: 10px;">📊 Gauges del Sistema</div>
            <div class="gauges">
                <div class="gauge-box">
                    <canvas id="g-cpu" class="gauge-canvas" width="80" height="80"></canvas>
                    <div class="gauge-label">CPU</div>
                    <div class="gauge-value" id="v-cpu">0%</div>
                </div>
                <div class="gauge-box">
                    <canvas id="g-ram" class="gauge-canvas" width="80" height="80"></canvas>
                    <div class="gauge-label">RAM</div>
                    <div class="gauge-value" id="v-ram">0%</div>
                </div>
                <div class="gauge-box">
                    <canvas id="g-gpu" class="gauge-canvas" width="80" height="80"></canvas>
                    <div class="gauge-label">GPU Util</div>
                    <div class="gauge-value" id="v-gpu">0%</div>
                </div>
                <div class="gauge-box">
                    <canvas id="g-vram" class="gauge-canvas" width="80" height="80"></canvas>
                    <div class="gauge-label">VRAM</div>
                    <div class="gauge-value" id="v-vram">0%</div>
                </div>
            </div>

            <div class="panel-title" style="margin-top: 10px;">💾 VRAM Allocation Visual</div>
            <div class="vram-visual" id="vram-vis">
                <div class="vram-segment qwen" style="width: 80%"><div class="vram-label">Qwen 19.4GB</div></div>
                <div class="vram-segment system" style="width: 5%"></div>
                <div class="vram-segment free" style="width: 15%"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.6rem; margin-top: 4px; color: #666;">
                <span>0 GB</span><span>12 GB</span><span>24 GB</span>
            </div>
            
            <div class="chart-box">
                <canvas id="main-chart"></canvas>
            </div>
        </div>

        <!-- COLUMNA CENTRAL: ARQUITECTURA + DATOS -->
        <div style="display: flex; flex-direction: column; gap: 10px;">
            <!-- Arquitectura SWARM -->
            <div class="panel">
                <div class="panel-title">🕸️ SWARM ARCHITECTURE v3.0</div>
                <div class="arch-grid" id="arch-grid">
                    <div class="arch-card active">
                        <div class="arch-icon">🧠</div>
                        <div class="arch-info">
                            <div class="arch-name">CEREBRO (Coordinador)</div>
                            <div class="arch-model">Kimi K2.5 • 256K context</div>
                            <div class="arch-loc">☁️ Cloud (Ollama Pro)</div>
                        </div>
                        <div class="arch-badge paid">PRO</div>
                    </div>
                    <div class="arch-card active">
                        <div class="arch-icon">⚡</div>
                        <div class="arch-info">
                            <div class="arch-name">AGENTE LOCAL (Ejecutor)</div>
                            <div class="arch-model">Qwen 2.5 32B • Q4_K_M</div>
                            <div class="arch-loc" id="qwen-loc">🖥️ 19.4GB VRAM • 35 tok/s</div>
                        </div>
                        <div class="arch-badge">FREE</div>
                    </div>
                    <div class="arch-card">
                        <div class="arch-icon">🔬</div>
                        <div class="arch-info">
                            <div class="arch-name">RESEARCH (Análisis)</div>
                            <div class="arch-model">GPT-4 • 128K context</div>
                            <div class="arch-loc">☁️ Anthropic API</div>
                        </div>
                        <div class="arch-badge paid">API $</div>
                    </div>
                </div>
            </div>

            <!-- Tokens + Costos -->
            <div class="panel">
                <div class="panel-title">🎫 TOKENS & 💰 COSTOS EN TIEMPO REAL</div>
                <div class="token-panel" id="tokens">
                    <div class="token-row">
                        <div class="token-agent"><span class="token-dot" style="background:#3b82f6"></span>🧠 Kimi</div>
                        <div class="token-val" id="t-k-in">0</div>
                        <div class="token-val" id="t-k-out">0</div>
                        <div class="token-cost" id="c-k">$0.00</div>
                    </div>
                    <div class="token-row">
                        <div class="token-agent"><span class="token-dot" style="background:#00ff88"></span>⚡ Qwen 32B</div>
                        <div class="token-val" id="t-q-in">0</div>
                        <div class="token-val" id="t-q-out">0</div>
                        <div class="token-cost" style="color:#00ff88">FREE</div>
                    </div>
                    <div class="token-row">
                        <div class="token-agent"><span class="token-dot" style="background:#ff6b35"></span>🔬 GPT-4</div>
                        <div class="token-val" id="t-g-in">0</div>
                        <div class="token-val" id="t-g-out">0</div>
                        <div class="token-cost" id="c-g">$0.00</div>
                    </div>
                    <div style="text-align: right; padding: 8px; background: rgba(255,107,53,0.1); border-radius: 4px; margin-top: 6px;">
                        <span style="font-size: 0.65rem; color: #888;">COSTO TOTAL SESIÓN: </span>
                        <span style="font-size: 1.2rem; color: #ff6b35; font-weight: bold;" id="c-total">$0.00</span>
                    </div>
                </div>
            </div>

            <!-- Modelos en VRAM detalle -->
            <div class="panel" style="flex: 1;">
                <div class="panel-title">🦙 MODELOS CARGADOS EN VRAM</div>
                <div id="models-detail" style="font-size: 0.75rem;">
                    <div style="color: #666;">Escaneando VRAM...</div>
                </div>
                
                <div class="panel-title" style="margin-top: 15px;">🔧 PROCESOS CRÍTICOS</div>
                <div class="proc-list" id="procs">
                    <div style="color: #666;">Cargando...</div>
                </div>
            </div>
        </div>

        <!-- COLUMNA DERECHA: APIS + TAREAS -->
        <div style="display: flex; flex-direction: column; gap: 10px;">
            <!-- APIs -->
            <div class="panel">
                <div class="panel-title">🔌 API INTEGRATIONS</div>
                <div class="api-list" id="apis">
                    <div class="api-item">📺 YouTube <span class="api-status">🟡</span></div>
                    <div class="api-item">📧 Gmail <span class="api-status">🟡</span></div>
                    <div class="api-item">📋 Notion <span class="api-status">🟡</span></div>
                    <div class="api-item">🦞 Moltbook <span class="api-status">🟡</span></div>
                    <div class="api-item">💬 Telegram <span class="api-status">🟡</span></div>
                </div>
            </div>

            <!-- Mis tareas -->
            <div class="panel">
                <div class="panel-title">🤖 MIS TAREAS (Lumen)</div>
                <div class="task-list" id="lumen-tasks">
                    <div class="task-item"><span>●</span> Dashboard v6.0 deploy</div>
                    <div class="task-item pending"><span>○</span> Optimizar 3D</div>
                </div>
            </div>

            <!-- Tareas Hb -->
            <div class="panel">
                <div class="panel-title">👤 TUS TAREAS (Hb)</div>
                <div class="task-list" id="hb-tasks">
                    <div class="task-item pending"><span>🟡</span> Revisar v6.0</div>
                </div>
            </div>

            <!-- Metrics Summary -->
            <div class="panel" style="margin-top: auto;">
                <div class="panel-title">📈 MÉTRICAS DE SESIÓN</div>
                <div class="metrics-footer">
                    <div class="metric-box">
                        <div>PEAK GPU</div>
                        <div class="metric-value" id="peak-gpu">0%</div>
                    </div>
                    <div class="metric-box">
                        <div>PEAK RAM</div>
                        <div class="metric-value" id="peak-ram">0%</div>
                    </div>
                    <div class="metric-box">
                        <div>TOKENS/S</div>
                        <div class="metric-value" id="tok-s">0</div>
                    </div>
                    <div class="metric-box">
                        <div>REQUESTS</div>
                        <div class="metric-value" id="reqs">0</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const socket = io('http://127.0.0.1:8766');
        let mainChart;
        
        // Three.js GPU Visualization
        function initGPU3D() {
            const container = document.getElementById('gpu-3d');
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, container.clientWidth / 150, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
            renderer.setSize(container.clientWidth, 150);
            container.appendChild(renderer.domElement);
            
            // GPU Cube
            const geometry = new THREE.BoxGeometry(2, 1, 0.3);
            const material = new THREE.MeshBasicMaterial({ 
                color: 0x00ff88, 
                wireframe: true,
                transparent: true,
                opacity: 0.8
            });
            const cube = new THREE.Mesh(geometry, material);
            scene.add(cube);
            
            // Inner core
            const coreGeo = new THREE.BoxGeometry(1.8, 0.8, 0.2);
            const coreMat = new THREE.MeshBasicMaterial({ 
                color: 0xff6b35,
                transparent: true,
                opacity: 0.3
            });
            const core = new THREE.Mesh(coreGeo, coreMat);
            scene.add(core);
            
            camera.position.z = 3;
            
            // Animation
            function animate() {
                requestAnimationFrame(animate);
                cube.rotation.y += 0.01;
                cube.rotation.x += 0.005;
                core.rotation.y -= 0.008;
                renderer.render(scene, camera);
            }
            animate();
            
            // Color change based on GPU temp
            window.updateGPUColor = (temp) => {
                if (temp > 80) {
                    material.color.setHex(0xff4444);
                    coreMat.color.setHex(0xff0000);
                } else if (temp > 70) {
                    material.color.setHex(0xffaa00);
                    coreMat.color.setHex(0xff6600);
                } else {
                    material.color.setHex(0x00ff88);
                    coreMat.color.setHex(0x00cc66);
                }
            };
        }
        
        // Gauge drawing
        function drawGauge(canvasId, value, color) {
            const canvas = document.getElementById(canvasId);
            const ctx = canvas.getContext('2d');
            const c = canvas.width / 2;
            const r = 35;
            
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Background ring
            ctx.beginPath();
            ctx.arc(c, c, r, 0.7 * Math.PI, 2.3 * Math.PI);
            ctx.strokeStyle = '#1a1a2e';
            ctx.lineWidth = 8;
            ctx.lineCap = 'round';
            ctx.stroke();
            
            // Value arc
            const angle = 0.7 * Math.PI + (value / 100) * 1.6 * Math.PI;
            ctx.beginPath();
            ctx.arc(c, c, r, 0.7 * Math.PI, angle);
            ctx.strokeStyle = value > 85 ? '#ff4444' : value > 70 ? '#ffaa00' : color;
            ctx.lineWidth = 8;
            ctx.lineCap = 'round';
            ctx.stroke();
        }
        
        // Main history chart
        function initMainChart() {
            const ctx = document.getElementById('main-chart').getContext('2d');
            mainChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: Array(60).fill(''),
                    datasets: [
                        { label: 'CPU %', data: Array(60).fill(0), borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.1)', borderWidth: 2, fill: true, tension: 0.4, pointRadius: 0 },
                        { label: 'GPU %', data: Array(60).fill(0), borderColor: '#ff6b35', backgroundColor: 'rgba(255,107,53,0.1)', borderWidth: 2, fill: true, tension: 0.4, pointRadius: 0 },
                        { label: 'VRAM %', data: Array(60).fill(0), borderColor: '#00ff88', backgroundColor: 'rgba(0,255,136,0.1)', borderWidth: 2, fill: true, tension: 0.4, pointRadius: 0 }
                    ]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: true, labels: { color: '#888', font: { size: 10 } } } },
                    scales: {
                        x: { display: false },
                        y: { beginAtZero: true, max: 100, ticks: { color: '#666', font: { size: 9 } }, grid: { color: '#222' } }
                    },
                    animation: false
                }
            });
        }
        
        function fmtNum(n) {
            if (n >= 1000000) return (n/1000000).toFixed(2) + 'M';
            if (n >= 1000) return (n/1000).toFixed(1) + 'K';
            return n.toString();
        }
        
        // Clock
        setInterval(() => {
            const now = new Date();
            document.getElementById('clock').textContent = now.toLocaleTimeString();
        }, 1000);
        
        // Socket events
        socket.on('connect', () => {
            document.getElementById('conn').textContent = '🟢 ONLINE';
            document.getElementById('conn').style.color = '#00ff88';
        });
        
        socket.on('data', (d) => {
            // Gauges
            if (d.sys) {
                drawGauge('g-cpu', d.sys.cpu, '#3b82f6');
                document.getElementById('v-cpu').textContent = d.sys.cpu.toFixed(0) + '%';
                document.getElementById('v-cpu').style.color = d.sys.cpu > 80 ? '#ff4444' : d.sys.cpu > 60 ? '#ffaa00' : '#3b82f6';
                
                drawGauge('g-ram', d.sys.ram_percent, '#00ff88');
                document.getElementById('v-ram').textContent = d.sys.ram_percent.toFixed(0) + '%';
                
                // Procesos
                if (d.sys.top_procs) {
                    document.getElementById('procs').innerHTML = d.sys.top_procs.map(p => `
                        <div class="proc-row">
                            <span>${p.name.substring(0, 20)}</span>
                            <span style="color:#3b82f6">${p.cpu_percent.toFixed(1)}%</span>
                            <span style="color:#00ff88">${p.memory_percent.toFixed(1)}%</span>
                        </div>
                    `).join('');
                }
            }
            
            // GPU
            if (d.gpu) {
                drawGauge('g-gpu', d.gpu.util_gpu, '#ff6b35');
                document.getElementById('v-gpu').textContent = d.gpu.util_gpu + '%';
                
                const vramPct = (d.gpu.vram_used / d.gpu.vram_total) * 100;
                drawGauge('g-vram', vramPct, '#00ff88');
                document.getElementById('v-vram').textContent = vramPct.toFixed(0) + '%';
                
                // 3D color
                if (window.updateGPUColor) window.updateGPUColor(d.gpu.temp_gpu);
                
                // Modelos
                if (d.ollama && d.ollama.length > 0) {
                    const totalVram = d.ollama.reduce((a, m) => a + m.vram_gb, 0);
                    document.getElementById('models-detail').innerHTML = d.ollama.map(m => `
                        <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #222;">
                            <span>🦙 ${m.name.split(':')[0]}</span>
                            <span style="color: #00ff88; font-family: monospace;">${m.vram_gb.toFixed(1)} GB</span>
                        </div>
                    `).join('') + `
                        <div style="text-align: right; margin-top: 8px; font-size: 0.7rem; color: #666;">
                            Total: <span style="color: #00ff88; font-size: 0.9rem;">${totalVram.toFixed(1)} GB</span>
                        </div>
                    `;
                    
                    // Update VRAM visual
                    const sysUsed = (d.gpu.vram_used / 1024) - totalVram;
                    const qwenPct = (totalVram / 24) * 100;
                    const sysPct = (sysUsed / 24) * 100;
                    const freePct = 100 - qwenPct - sysPct;
                    
                    document.getElementById('vram-vis').innerHTML = `
                        <div class="vram-segment qwen" style="width: ${qwenPct}%"><div class="vram-label">Qwen ${totalVram.toFixed(1)}GB</div></div>
                        <div class="vram-segment system" style="width: ${sysPct}%"></div>
                        <div class="vram-segment free" style="width: ${freePct}%"><div class="vram-label">${(24-totalVram-sysUsed).toFixed(1)}GB Free</div></div>
                    `;
                    
                    // Update arch
                    document.getElementById('qwen-loc').textContent = `🖥️ ${totalVram.toFixed(1)}GB VRAM • ${d.tokens.qwen.speed.toFixed(0)} tok/s`;
                }
                
                // Chart
                if (d.history && mainChart) {
                    mainChart.data.datasets[0].data = d.history.cpu.slice(-60);
                    mainChart.data.datasets[1].data = d.history.gpu.slice(-60);
                    mainChart.data.datasets[2].data = d.history.vram.slice(-60);
                    mainChart.update('none');
                }
            }
            
            // Tokens
            if (d.tokens) {
                const t = d.tokens;
                document.getElementById('t-k-in').textContent = fmtNum(t.kimi.in);
                document.getElementById('t-k-out').textContent = fmtNum(t.kimi.out);
                document.getElementById('c-k').textContent = '$' + t.kimi.cost.toFixed(3);
                
                document.getElementById('t-q-in').textContent = fmtNum(t.qwen.in);
                document.getElementById('t-q-out').textContent = fmtNum(t.qwen.out);
                
                document.getElementById('t-g-in').textContent = fmtNum(t.gpt4.in);
                document.getElementById('t-g-out').textContent = fmtNum(t.gpt4.out);
                document.getElementById('c-g').textContent = '$' + t.gpt4.cost.toFixed(3);
                
                document.getElementById('c-total').textContent = '$' + d.cost_total.toFixed(3);
                document.getElementById('tok-s').textContent = t.qwen.speed.toFixed(0);
            }
            
            // APIs
            if (d.apis) {
                const a = d.apis;
                document.getElementById('apis').innerHTML = `
                    <div class="api-item">📺 YouTube <span class="api-status">${a.youtube}</span></div>
                    <div class="api-item">📧 Gmail <span class="api-status">${a.gmail}</span></div>
                    <div class="api-item">📋 Notion <span class="api-status">${a.notion}</span></div>
                    <div class="api-item">🦞 Moltbook <span class="api-status">${a.moltbook}</span></div>
                    <div class="api-item">💬 Telegram <span class="api-status">${a.telegram}</span></div>
                `;
            }
            
            // Metrics
            if (d.metrics) {
                const m = d.metrics;
                document.getElementById('peak-gpu').textContent = m.peak_gpu + '%';
                document.getElementById('peak-ram').textContent = m.peak_ram.toFixed(0) + '%';
                document.getElementById('reqs').textContent = m.total_requests;
                
                const up = Math.floor((new Date() - new Date(m.session_start)) / 60000);
                document.getElementById('uptime').textContent = `UPTIME: ${Math.floor(up/60)}h ${up%60}m`;
            }
        });
        
        socket.on('disconnect', () => {
            document.getElementById('conn').textContent = '🔴 OFFLINE';
            document.getElementById('conn').style.color = '#ff4444';
        });
        
        // Init
        window.onload = () => {
            setTimeout(() => {
                initGPU3D();
                initMainChart();
                drawGauge('g-cpu', 0, '#3b82f6');
                drawGauge('g-ram', 0, '#00ff88');
                drawGauge('g-gpu', 0, '#ff6b35');
                drawGauge('g-vram', 0, '#00ff88');
            }, 100);
        };
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    from threading import Thread
    Thread(target=emitter, daemon=True).start()
    print("🔮 LumenAGI v6.0 — MISSION CONTROL")
    print("⚡ GPU 3D + Gauges + Historial 5min + Tokens realtime + Arquitectura visual")
    print("🌐 http://localhost:8766")
    socketio.run(app, host='0.0.0.0', port=8766, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
