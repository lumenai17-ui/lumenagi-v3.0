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