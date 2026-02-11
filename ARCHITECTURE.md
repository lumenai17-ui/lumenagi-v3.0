# LumenAGI Architecture v2.0 (Feb 11, 2026)

## Clean Architecture — Post Crash Recovery

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LUMENAGI SYSTEM                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────┐                                │
│  │         CEREBRO — MAIN AGENT           │                                │
│  │    Model: kimi-k2.5 (OpenRouter)        │                                │
│  │    Role: Coordinator, Strategy          │
│  │    VRAM: ~0GB (Cloud)                  │
│  └──────────────┬──────────────────────────┘                                │
│                 │                                                            │
│     ┌───────────┼───────────┐                                               │
│     ▼           ▼           ▼                                               │
│  ┌───────┐  ┌───────┐  ┌───────┐                                          │
│  │       │  │       │  │       │        GPU VRAM: 24GB                     │
│  │Qwen32 │  │Qwen32 │  │Qwen32 │        ┌─────────────┐                     │
│  │Research│ │ Build │  │Create │        │  RESERVED   │                     │
│  │       │  │       │  │       │        │   20GB      │                     │
│  │ Local │  │ Local │  │ Local │        │  qwen2.5:32b│ ◀── ALWAYS ON      │
│  │~6.6GB │  │~6.6GB │  │~6.6GB │        │   4096 ctx  │                     │
│  └───────┘  └───────┘  └───────┘        │  24h keepalive                  │
│                                          └─────────────┘                     │
│                                                 │                            │
│  ┌─────────────────────────────────────────────┘                            │
│  │                                                                            │
│  ▼                                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │                 MULTIMEDIA — EXTERNAL APIs                       │         │
│  ├─────────────────────────────────────────────────────────────────┤         │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │         │
│  │  │   FLUX      │  │    SVD      │  │    TTS (ElevenLabs)     │ │         │
│  │  │  Replicate  │  │  Replicate  │  │        API              │ │         │
│  │  │  API        │  │  API        │  │                         │ │         │
│  │  │  (~$0.03/img│ │  (~$0.10/vid)│ │  (~$0.15/min)           │ │         │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘ │         │
│  └─────────────────────────────────────────────────────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Model | VRAM | Location | Tools | Role |
|-------|-------|------|----------|-------|------|
| **main** | kimi-k2.5:cloud | 0GB | OpenRouter | All | Cerebro, coordinador |
| **research-qwen32** | qwen2.5:32b | ~6.6GB | Local GPU (shared) | search, fetch, read, image | Investigación paralela |
| **build-qwen32** | qwen2.5:32b | ~6.6GB | Local GPU (shared) | exec, write, edit, read | Ejecución código |
| **create-qwen32** | qwen2.5:32b | ~6.6GB | Local GPU (shared) | exec, read, tts | Orchestration multimedia |

## GPU Allocation

```
RTX 3090 24GB:
├── Qwen2.5:32b (single instance) ........ 20GB [RESERVED]
│   └── Shared por: research, build, create
├── Display/Buffers ...................... 1GB
└── FREE for FLUX/SVD local (emergencias)  3GB

Note: Multimedia usa APIs externas por defecto.
      GPU local solo para emergencias/debug.
```

## API Budget

| Service | Cost | Monthly Est. |
|---------|------|--------------|
| OpenRouter (kimi-k2.5) | $3/M tokens | ~$20-30 |
| Replicate FLUX | $0.03/img | ~$5-10 |
| Replicate SVD | $0.10/video | ~$5 |
| ElevenLabs TTS | $0.15/min | ~$5 |
| **Total** | | **~$35-50/mo** |

## Keepalive Strategy

```bash
# Qwen32 — SIEMPRE ARRIBA
ollama run qwen2.5:32b --keepalive 24h

# No más de 5 minutos de inactividad
```

## Routing

```yaml
main (kimi):
  → research-qwen32: "Busca X"
  → build-qwen32: "Ejecuta Y"
  → create-qwen32: "Genera Z"

research-qwen32:
  returns: JSON findings
  
build-qwen32:
  returns: JSON results + file paths

create-qwen32:
  → Replicate API (FLUX): https://api.replicate.com
  → Replicate API (SVD): https://api.replicate.com
  → ElevenLabs TTS: https://api.elevenlabs.io
```

## Workspace Structure

```
~/.openclaw/
├── agents/
│   ├── main/                    # Cerebro (kimi-cloud)
│   ├── research-qwen32/agent/   # Research (local)
│   ├── build-qwen32/agent/      # Build (local)
│   └── create-qwen32/agent/     # Create (local)
├── workspace/
│   ├── dashboard/
│   │   ├── api.py              # Flask backend
│   │   └── index.html          # Mission Control UI
│   └── scripts/
│       ├── flux_replicate_api.py
│       └── svd_replicate_api.py
└── workspace-{research,build,create}/  # Sub-agent workspaces
```

## Recovery Checklist

- [x] Qwen2.5:32b loaded in VRAM (20GB)
- [x] Qwen32 keepalive: 24h
- [x] Sub-agents created with qwen32 config
- [x] External API scripts created
- [x] Main agent on kimi-cloud
- [ ] Dashboard updated for new agents
- [ ] Test end-to-end routing

---

*Architecture: Clean | GPU: Reserved for qwen32 only | APIs: External for multimedia*
