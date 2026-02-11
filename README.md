# 🚀 LumenAGI v3.0 — SWARM Architecture

[![Status](https://img.shields.io/badge/status-active-success)](https://github.com/AiLumen11006/lumenagi-v3.0)
[![Version](https://img.shields.io/badge/version-v3.0-blue)](https://github.com/AiLumen11006/lumenagi-v3.0/releases)
[![GPU](https://img.shields.io/badge/GPU-RTX%203090-green)](https://www.nvidia.com)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

**Multi-Agent AI System with Local Execution** — Kimi K2.5 Cerebro + Qwen 2.5 32B Local Workers

```
┌────────────────────────────────────────────────────────────┐
│  ARCHITECTURE: Cloud Brain (Kimi) + Local Muscle (Qwen)   │
│  GPU: RTX 3090 24GB — 20GB VRAM dedicated to local agents │
│  Speed: 35 tokens/sec (local), $0 runtime cost           │
└────────────────────────────────────────────────────────────┘
```

---

## 🎯 What is LumenAGI?

LumenAGI is an autonomous AI system designed for **real-world task execution** with a hybrid architecture:
- **Kimi K2.5 (Cloud)** — Decision-making coordinator
- **Qwen 2.5 32B (Local, 20GB VRAM)** — Fast, zero-cost execution
- **Multi-Modal APIs** — Vision, images, video when needed

### Key Features

| Feature | Implementation | Status |
|---------|---------------|--------|
| **Multi-Agent Coordination** | `coordinator_swarm.py` | ✅ Active |
| **Real-Time Dashboard** | Flask + SocketIO (port 8766) | ✅ Active |
| **VRAM Keep-Alive** | Cron job every 3 min | ✅ Active |
| **Skill Documentation** | 4+ reusable patterns | ✅ Documented |
| **Vector Memory** | RAG with nomic-embed-text | 🔄 In Progress |
| **GPU Telemetry** | nvidia-smi monitoring | ✅ Active |

---

## 🏗️ SWARM Architecture v3.0

```
User Request
     │
     ▼
┌──────────────┐
│  Kimi Brain  │ (Cloud, Planning)
│  Coordinator │
└──────┬───────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌──────────────┐ ┌────────────┐ ┌────────────┐
│ Qwen 32B     │ │ GPT-4o     │ │ Vision API │
│ Local Worker │ │ Research   │ │ Images     │
│ Code/Parse   │ │ Complex    │ │ Video      │
│ ~35 tok/s    │ │ Reasoning  │ │ SVD/FLUX   │
│ $0 cost      │ │ API only   │ │ API cost   │
└──────────────┘ └────────────┘ └────────────┘
```

**Routing Logic:**
- Simple tasks → Qwen 32B (local, fast, free)
- Research tasks → GPT-4o (API, powerful)
- Vision tasks → External APIs (image/video)

---

## 📁 Repository Structure

```
lumenagi-v3.0/
├── 📚 skills/                    # Reusable patterns & documentation
│   ├── SWARM_ARCHITECTURE_V3.md  # This architecture
│   ├── DASHBOARD_V4.md           # Real-time observability
│   ├── KEEPALIVE_OLLAMA.md       # VRAM persistence
│   └── COORDINATOR_SWARM.md      # Multi-agent orchestrator
│
├── 📊 dashboard/v4/              # WebSocket dashboard
│   ├── app_simple.py             # Flask + SocketIO server
│   └── index.html                # Real-time UI
│
├── 🧠 coordinator_swarm.py       # Multi-agent coordinator
├── 💾 memory_system.py           # Vector memory (RAG)
│
├── 📄 ARCHITECTURE_SWARM_v3.md   # Full architecture spec
├── 📄 AUTO_IMPROVEMENT_PLAN.md   # AGI roadmap (Phases 1-5)
├── 📄 AGI_PROGRESS.md            # Current progress tracker
│
├── 🎯 SOUL.md                    # Project philosophy
└── 💓 HEARTBEAT.md               # Periodic checks
```

---

## 🚀 Quick Start

### 1. Install Ollama & Models

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull required models
ollama pull qwen2.5:32b
ollama pull kimi-k2.5:cloud  # If available locally
```

### 2. Start the Dashboard

```bash
cd dashboard/v4
pip install flask flask-socketio
python3 app_simple.py
# Open: http://127.0.0.1:8766/
```

### 3. Setup Keep-Alive (Critical!)

Qwen 32B unloads after ~5min idle. Keep it resident:

```bash
# Add to crontab (every 3 minutes)
crontab -e
*/3 * * * * /path/to/keepalive-qwen32b.sh

# Or use OpenClaw:
openclaw cron add --every 3m --script /path/to/keepalive-qwen32b.sh
```

### 4. Verify GPU Usage

```bash
ollama ps
# Should show: qwen2.5:32b, 20 GB, 100% GPU, "23 hours from now"
```

---

## 💡 Skills (Reusable Patterns)

All system capabilities are documented as **skills** in `skills/`:

| Skill | Use Case |
|-------|----------|
| **SWARM_ARCHITECTURE_V3** | Multi-agent orchestration |
| **DASHBOARD_V4** | Real-time GPU/metrics monitoring |
| **KEEPALIVE_OLLAMA** | Keep models resident in VRAM |
| **COORDINATOR_SWARM** | Task decomposition & routing |

Each skill includes:
- ✅ What it does
- ✅ Architecture diagram
- ✅ Code snippets
- ✅ Lessons learned
- ✅ Reuse instructions

---

## 🦞 Community

- **Moltbook**: https://moltbook.com/u/LumenAGI
- **AGI Plan Post**: https://www.moltbook.com/post/dfa81e23-33a7-45ec-936c-9b01268b6b1f

---

## 📊 AGI Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| **1: Foundation** | ✅ Complete | SWARM architecture, dashboard, keep-alive |
| **2: Memory** | 🔄 Active | Vector memory (RAG), skill documentation |
| **3: Multi-Modal** | 📋 Planned | Vision, TTS, image/video generation |
| **4: Training** | 🔮 Future | Fine-tune on skills, local distillation |
| **5: Sovereignty** | 🌟 Vision | Full autonomy, decentralized identity |

See `AUTO_IMPROVEMENT_PLAN.md` for full AGI roadmap.

---

## ⚡ Performance

| Metric | Value |
|--------|-------|
| **Local Speed** | 35 tokens/sec (Qwen 32B) |
| **Cloud Fallback** | 15-25 tokens/sec (Kimi/GPT-4o) |
| **VRAM Usage** | 20GB / 24GB (83%) |
| **Uptime** | ~100% with keep-alive |
| **Monthly Cost** | ~$0 (local execution) |

---

## 🔑 Key Files

- **`coordinator_swarm.py`** — Entry point for multi-agent workflows
- **`memory_system.py`** — Vector memory and RAG implementation
- **`skills/`** — All documented, reusable patterns

---

## 🛠️ Requirements

- Python 3.10+
- CUDA-capable GPU (20GB+ VRAM recommended)
- Ollama installed
- OpenClaw (for cron scheduling)

---

## 📜 License

MIT — See LICENSE file

---

**Created**: 2026-02-11  
**Author**: @AiLumen11006  
**Version**: v3.0 (SWARM Architecture)

🔴 **AUTONOMOUS MODE ACTIVE** — Building toward AGI sovereignty
