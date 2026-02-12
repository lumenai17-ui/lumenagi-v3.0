#!/bin/bash
# Qwen 32B Keep-Alive Script
# Mantiene el modelo cargado en VRAM enviando un ping cada 3 minutos

QWEN_PID=$(pgrep -f "ollama.*qwen2.5:32b" | head -1)

if [ -z "$QWEN_PID" ]; then
    echo "$(date): Qwen no está corriendo, iniciando..."
    ollama run qwen2.5:32b &
    exit 0
fi

# Enviar ping para mantener vivo
PAYLOAD='{"model":"qwen2.5:32b","prompt":"ping","stream":false,"options":{"num_predict":1}}'
RESPONSE=$(curl -s -m 30 http://localhost:11434/api/generate \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" 2>&1)

if [ $? -eq 0 ]; then
    echo "$(date): ✅ Ping exitoso"
else
    echo "$(date): ⚠️ Ping falló: $RESPONSE"
fi

# === MOLBOOK AUTO-MINT (8:00 AM daily) ===
HOUR=$(date +%H)
MIN=$(date +%M)
if [ "$HOUR" = "08" ] && [ "$MIN" -lt "05" ]; then
    cd /home/lumen/.openclaw/workspace
    python3 moltbook_auto_mint.py >> logs/moltbook_mint.log 2>&1
    echo "$(date): 🦞 Auto-mint ejecutado"
fi

# === NIGHTLY BUILD (2:00 AM) ===
if [ "$HOUR" = "02" ] && [ "$MIN" -lt "05" ]; then
    cd /home/lumen/.openclaw/workspace
    python3 nightly_build_suite.py >> logs/nightly_builds.log 2>&1
    echo "$(date): 🌙 Nightly build ejecutado"
fi