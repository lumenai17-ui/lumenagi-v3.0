#!/usr/bin/env python3
"""
LumenAGI Dashboard v4.0 — Definitive Agent Observatory
Hybrid: GPU-hot realtime + Langfuse observability + Mission Control SWARM
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from flask import Flask, jsonify, render_template, send_from_directory
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

BASE_DIR = Path(__file__).parent
AGENTS_DIR = Path.home() / ".openclaw/agents"

@dataclass
class GPUMetrics:
    timestamp: str
    device: str
    used_mb: int
    free_mb: int
    total_mb: int
    utilization: int
    temperature: int
    power_draw: float
    clock_graphics: int
    clock_memory: int
    processes: List[dict]

@dataclass 
class AgentTrace:
    agent_id: str
    model: str
    task: str
    status: str
    start_time: str
    end_time: Optional[str]
    tokens_in: int
    tokens_out: int
    cost_usd: float
    latency_ms: int

@dataclass
class SystemState:
    gpu: Optional[GPUMetrics]
    agents: List[AgentTrace]
    swarm_status: dict

# ============================================================================
# GPU MONITORING (adaptado de gpu-hot: NVML interface)
# ============================================================================

def get_gpu_metrics() -> Optional[GPUMetrics]:
    """Captura métricas GPU en tiempo real usando nvidia-smi"""
    try:
        # Query extendido: memoria, utilización, temperatura, power, clocks, procesos
        result = subprocess.run([
            'nvidia-smi', 
            '--query-gpu=timestamp,name,memory.used,memory.free,memory.total,utilization.gpu,temperature.gpu,power.draw,clocks.gr,clocks.mem',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True, timeout=3)
        
        if result.returncode != 0:
            return None
            
        parts = result.stdout.strip().split(', ')
        timestamp, device, used, free, total, util, temp, power, clock_g, clock_m = parts
        
        # Procesos activos en GPU
        proc_result = subprocess.run([
            'nvidia-smi',
            '--query-compute-apps=pid,process_name,used_memory',
            '--format=csv,noheader'
        ], capture_output=True, text=True, timeout=3)
        
        processes = []
        if proc_result.returncode == 0:
            for line in proc_result.stdout.strip().split('\n'):
                if line:
                    pid, name, mem = line.split(', ')
                    processes.append({
                        'pid': pid,
                        'name': name.split('/')[-1][:30],  # Solo basename, truncado
                        'memory_mb': int(mem)
                    })
        
        return GPUMetrics(
            timestamp=timestamp,
            device=device,
            used_mb=int(used),
            free_mb=int(free),
            total_mb=int(total),
            utilization=int(util),
            temperature=int(temp),
            power_draw=float(power) if power != '[N/A]' else 0.0,
            clock_graphics=int(clock_g),
            clock_memory=int(clock_m),
            processes=processes[:5]  # Top 5 procesos
        )
    except Exception as e:
        print(f"GPU metrics error: {e}")
        return None

def get_ollama_models() -> List[str]:
    """Detecta modelos cargados en ollama"""
    try:
        result = subprocess.run(['ollama', 'ps'], capture_output=True, text=True, timeout=5)
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        models = []
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    models.append(parts[0])
        return models
    except:
        return []

# ============================================================================
# AGENT OBSERVABILITY (adaptado de Langfuse: traces, costs)
# ============================================================================

def get_agent_traces(limit: int = 10) -> List[AgentTrace]:
    """Obtiene trazas recientes de agentes desde filesystem"""
    traces = []
    agents = ['main', 'research-qwen32', 'build-qwen32', 'create-qwen32']
    
    for agent_name in agents:
        agent_dir = AGENTS_DIR / agent_name / "sessions"
        if not agent_dir.exists():
            continue
            
        # Buscar sesiones recientes
        sessions = sorted(agent_dir.glob("*.jsonl"), key=os.path.getmtime, reverse=True)
        
        for session_file in sessions[:2]:  # Últimas 2 sesiones
            try:
                with open(session_file, 'r') as f:
                    lines = f.readlines()
                    if not lines:
                        continue
                    
                    # Parsear última entrada para métricas
                    last_entry = json.loads(lines[-1])
                    
                    traces.append(AgentTrace(
                        agent_id=agent_name,
                        model=last_entry.get('model', 'unknown'),
                        task=last_entry.get('task', 'unknown')[:50],
                        status='running' if last_entry.get('status') == 'in_progress' else 'completed',
                        start_time=last_entry.get('start_time', datetime.now().isoformat()),
                        end_time=last_entry.get('end_time'),
                        tokens_in=last_entry.get('tokens_in', 0),
                        tokens_out=last_entry.get('tokens_out', 0),
                        cost_usd=last_entry.get('cost_usd', 0.0),
                        latency_ms=last_entry.get('latency_ms', 0)
                    ))
            except:
                pass
    
    return sorted(traces, key=lambda x: x.start_time, reverse=True)[:limit]

def get_swarm_status() -> dict:
    """Estado del SWARM de agentes"""
    status = {
        'coordinator': 'main',
        'coordinator_model': 'kimi-2.5:cloud',
        'workers': [],
        'gpu_exclusive': 'qwen2.5:32b',
        'multimedia': 'external-apis'
    }
    
    for agent_name in ['research-qwen32', 'build-qwen32', 'create-qwen32']:
        config_file = AGENTS_DIR / agent_name / "/agent/openclaw.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    status['workers'].append({
                        'name': agent_name,
                        'model': config.get('model', 'unknown'),
                        'role': agent_name.split('-')[0],
                        'parent': config.get('parent', 'main')
                    })
            except:
                pass
    
    return status

# ============================================================================
# WEBSOCKET REALTIME (adaptado de gpu-hot: sub-500ms updates)
# ============================================================================

@sock.route('/ws')
def websocket_handler(ws):
    """WebSocket para actualizaciones en tiempo real (0.5s refresh)"""
    import time
    print("[WS] Client connected")
    try:
        while True:
            # Obtener métricas
            gpu_data = get_gpu_metrics()
            ollama_data = get_ollama_models()
            traces_data = get_agent_traces(5)
            swarm_data = get_swarm_status()
            
            data = {
                'timestamp': datetime.now().isoformat(),
                'gpu': asdict(gpu_data) if gpu_data else None,
                'ollama_models': ollama_data,
                'agents': [asdict(t) for t in traces_data],
                'swarm': swarm_data
            }
            
            json_data = json.dumps(data)
            print(f"[WS] Sending: {len(json_data)} bytes, GPU: {data['gpu'] is not None}, Ollama: {len(ollama_data)} models")
            ws.send(json_data)
            time.sleep(0.5)  # 500ms update rate
    except Exception as e:
        print(f"[WS] Error: {e}")
        import traceback
        traceback.print_exc()

# ============================================================================
# HTTP API ENDPOINTS
# ============================================================================

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/api/v1/metrics')
def api_metrics():
    """API REST para métricas actuales"""
    gpu = get_gpu_metrics()
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'gpu': asdict(gpu) if gpu else None,
        'ollama': get_ollama_models(),
        'swarm': get_swarm_status()
    })

@app.route('/api/v1/agents')
def api_agents():
    """API para estado de agentes"""
    return jsonify({
        'agents': [asdict(t) for t in get_agent_traces(50)],
        'swarm_config': get_swarm_status()
    })

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(BASE_DIR / 'static', filename)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Flask-Sock requiere configuración específica
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    
    print("🚀 LumenAGI Dashboard v4.0 — Definitive Observatory")
    print("📡 WebSocket: ws://127.0.0.1:8766/ws")
    print("📊 API: http://127.0.0.1:8766/api/v1/")
    print("🌐 Dashboard: http://127.0.0.1:8766/")
    print("")
    print("Features:")
    print("  ✓ GPU realtime (0.5s) — NVML via nvidia-smi")
    print("  ✓ Agent observability — traces, costs, latency")
    print("  ✓ SWARM topology — visual flow")
    print("  ✓ 128K context support monitoring")
    
    server = pywsgi.WSGIServer(('127.0.0.1', 8766), app, handler_class=WebSocketHandler)
    server.serve_forever()
