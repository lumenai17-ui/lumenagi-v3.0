# 🔮 LumenAGI v4.1 — Definitive Agent Observatory

> Sistema SWARM autónomo con Cerebro (kimi-2.5) + Workers (qwen32) + Dashboard realtime

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    LUMENAGI v4.1                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🧠 CEREBRO (kimi-2.5 cloud)                                │
│     Lumen — Coordinador principal                           │
│     │                                                       │
│     ├──→ 🔍 @research — qwen32 (investigación)              │
│     ├──→ 🔨 @build — qwen32 (construcción)                  │
│     └──→ 🎨 @create — qwen32 (multimedia + APIs)            │
│                                                             │
│  📊 Dashboard: http://127.0.0.1:8766/                       │
│  📱 Telegram: @Lumeniabot                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

```bash
# One-command deploy
cd ~/.openclaw/workspace
./scripts/deploy_all.sh

# Check status
./scripts/health_check.sh
```

## 📦 Componentes

### 1. Dashboard v4.1 — Definitive Observatory
- **URL**: http://127.0.0.1:8766/
- **Stack**: Flask + WebSocket (gevent)
- **Features**:
  - GPU telemetry en tiempo real (500ms)
  - Agent traces con cost tracking
  - SWARM topology visualization
  - Charts GPU/Agent history
  - Auto-reconnect WebSocket

### 2. Telegram Bridge — @Lumeniabot
- **Framework**: aiogram 3.x
- **Tipo**: Webhook independiente
- **Routing por mención**:
  - `@research` → qwen32 investigación
  - `@build` → qwen32 construcción
  - `@create` → qwen32 + APIs multimedia
  - `@main` → kimí-2.5 coordinador
- **Comandos**: /start, /help, /status, /agents

### 3. Health Check System
- **Script**: `scripts/health_check.sh`
- **Frecuencia**: Recomendado cada 5 minutos (cron)
- **Monitorea**:
  - Dashboard v4 (HTTP)
  - Telegram Bridge (proceso)
  - OpenClaw Gateway (HTTP)
  - Ollama API (GPU models)

## 📁 Estructura

```
~/.openclaw/workspace/
├── dashboard/v4/              # Dashboard Flask + WebSocket
│   ├── app.py                 # Backend
│   ├── index.html             # Enhanced v4.1 UI
│   ├── enhanced.js            # Features avanzadas
│   └── requirements.txt       # Dependencias
│
├── telegram_bridge/           # Bridge aiogram Telegram
│   ├── telegram_bridge.py     # Bot handler
│   └── requirements.txt       # aiogram, aiohttp
│
├── agents/                    # Configuraciones OpenClaw
│   ├── main/                  # Cerebro coordinator
│   ├── research-qwen32/       # Worker investigación
│   ├── build-qwen32/          # Worker construcción
│   └── create-qwen32/         # Worker multimedia
│
├── scripts/                   # Utilidades
│   ├── deploy_all.sh          # Deploy one-command
│   ├── health_check.sh        # Health monitoring
│   └── restart_dashboard.sh   # Restart helper
│
├── logs/                      # Logs centralizados
├── skills/                    # Documentación de skills
├── memory/                    # Notas diarias
└── README.md                  # Este archivo
```

## 🛠️ Dependencias

```bash
# Python packages (usar --break-system-packages si es necesario)
pip install flask flask-sock gevent gevent-websocket
pip install aiogram aiohttp
```

## 🎮 Uso

### Dashboard
1. Abrir: http://127.0.0.1:8766/
2. Ver GPU metrics en tiempo real
3. Ver SWARM topology con agentes activos
4. Ver traces de ejecución con costos

### Telegram
1. Buscar: @Lumeniabot
2. Enviar: `@research busca información sobre...`
3. Esperar respuesta (10-60s dependiendo del agente)

### API Directa
```bash
# Métricas actuales
curl http://127.0.0.1:8766/api/v1/metrics

# Health
curl http://127.0.0.1:8766/api/v1/health

# GPU
curl http://127.0.0.1:8766/api/v1/gpu
```

## 📊 Monitoreo

### Health Check Manual
```bash
./scripts/health_check.sh
tail -f logs/health_check.log
```

### Cron (Opcional)
```cron
# Checkear cada 5 minutos
*/5 * * * * /home/lumen/.openclaw/workspace/scripts/health_check.sh
```

## 🔧 Troubleshooting

### Dashboard no responde
```bash
./scripts/health_check.sh  # Auto-restart incluido
# O manual:
pkill -f v4/app.py
cd dashboard/v4 && python3 app.py
```

### Telegram Bridge caído
```bash
pkill -f telegram_bridge.py
nohup python3 telegram_bridge/telegram_bridge.py >> logs/telegram_bridge.log 2>&1 &
```

### GPU no detectada
```bash
nvidia-smi  # Verificar driver
ollama ps   # Verificar modelos cargados
```

## 📡 Especificaciones Técnicas

| Componente | Valor |
|------------|-------|
| **GPU** | RTX 3090 24GB |
| **VRAM Reservado** | 20GB (qwen32 exclusivo) |
| **Context Window** | 128K tokens |
| **WebSocket Update** | 500ms |
| **Models** | kimi-2.5 (cloud), qwen2.5:32b (local) |
| **Dashboard Port** | 8766 |
| **Gateway Port** | 18789 |

## 🔄 Modo Autónomo

Cuando el usuario está ausente, el sistema:
1. Mantiene todos los servicios activos
2. Ejecuta health checks periódicos
3. Documenta progreso en `memory/`
4. Mejora continuamente el código
5. Guarda logs de todas las operaciones

## 📄 Licencia

Sistema interno LumenAGI — Uso personal autorizado.

---

**Versión**: v4.1  
**Fecha**: 2026-02-11  
**Modo**: 🔴 Autónomo Activo  
