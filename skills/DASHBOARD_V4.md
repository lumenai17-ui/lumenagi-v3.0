# Skill: Dashboard v4.1 SocketIO

## What It Does
Dashboard real-time para observabilidad del sistema LumenAGI. Muestra GPU, VRAM, modelos Ollama, agentes SWARM, y trazas en tiempo real.

## Architecture
```
Flask + SocketIO → WebSocket a navegador
     │
     ├── nvidia-smi (GPU metrics)
     ├── Ollama API (/api/ps)
     └── Background thread (emite cada 1s)
```

## Code
```python
# server/app_simple.py
socketio = SocketIO(app, cors_allowed_origins="*")

def emit_metrics():
    while True:
        gpu = get_gpu_metrics()  # nvidia-smi
        ollama = get_ollama_models()
        socketio.emit('metrics', {'gpu': gpu, 'ollama': ollama})
        time.sleep(1)
```

## Installation
```bash
cd /home/lumen/.openclaw/workspace/dashboard/v4
pip install flask flask-socketio
python3 app_simple.py
# Open: http://127.0.0.1:8766/
```

## Lessons Learned
- Puerto 8766 puede estar ocupado → matar procesos viejos
- Werkzeug necesita `allow_unsafe_werkzeug=True` para dev
- SocketIO más estable que WebSocket nativo
- Frontend en `index.html` con CDN Socket.IO client

## Reuse
Copy `dashboard/v4/` structure for any real-time monitoring:
- Background emitter thread
- SocketIO broadcast
- Chart.js for visualizations
