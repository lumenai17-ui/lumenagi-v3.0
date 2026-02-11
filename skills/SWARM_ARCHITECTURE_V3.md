# Skill: SWARM Architecture v3.0

## What It Does
Arquitectura multi-agente que separa roles entre modelo cerebro (Kimi cloud) y modelo ejecutor (Qwen 32B local). Optimiza costos y velocidad.

## Architecture
```
Usuario → Kimi (Cerebro/Cloud) → Decide plan
              │
              ├── Simple → Qwen 32B (Local, $0, ~35 tok/s)
              ├── Complejo → GPT-4o (API $)
              └── Imagen → Vision APIs
```

## Configuration
File: `~/.openclaw/openclaw.json`
- `main`: `ollama/kimi-k2.5:cloud`
- `subagents`: `ollama/qwen2.5:32b`
- `research`: `openai/gpt-4o`
- `build`/`create`: `ollama/qwen2.5:32b`

## Code
```python
# Test Qwen 32B direct
curl http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5:32b","prompt":"hello"}'

# Expected: 35 tok/s, ~20GB VRAM
```

## Lessons Learned
- Qwen 32B necesita keep-alive (5min timeout default)
- PyTorch carga lento la primera vez (~2-3 min)
- `allow_unsafe_werkzeug=True` para Flask dev

## Reuse
Use this architecture whenever you need:
- Fast local responses (Qwen)
- Complex reasoning fallback (GPT-4o)
- Zero-cost simple tasks (35 tok/s local)
