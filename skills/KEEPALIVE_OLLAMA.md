# Skill: Keep-Alive for Ollama Models

## What It Does
Mantiene modelos Ollama cargados en VRAM indefinidamente enviando pings periódicos. Evita el timeout de 5 minutos de inactividad.

## Architecture
```
Cron (cada 3 min) → Script → curl Ollama API
                                      │
                              keep_alive: -1 (modelo residente)
```

## Code
```bash
#!/bin/bash
# scripts/keepalive-qwen32b.sh
PAYLOAD='{"model":"qwen2.5:32b","prompt":"ping","options":{"num_predict":1}}'
curl -s http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"
```

## Installation
```bash
# Agregar a cron (cada 3 min)
crontab -e
*/3 * * * * /home/lumen/.openclaw/scripts/keepalive-qwen32b.sh

# O usar OpenClaw cron:
openclaw cron add --every 3m --script /path/to/keepalive.sh
```

## Verification
```bash
ollama ps
# Should show: qwen2.5:32b, 20 GB, 100% GPU, "23 hours from now"
```

## Lessons Learned
- `ollama run` sin prompt no carga en VRAM
- Primer request tarda ~2-3 min (carga inicial)
- `keep_alive: -1` en OpenAI API mantiene modelo
- Timeout default Ollama: ~5 min de inactividad

## Reuse
Apply to any Ollama model that needs to stay resident:
- Large models (13B+) with slow load times
- Production agents requiring low latency
- Multi-model setups where unload/reload is expensive
