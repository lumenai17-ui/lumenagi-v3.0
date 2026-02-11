#!/bin/bash
# Monitoreo de GPU durante test multi-agente

echo "⏱️ Iniciando monitoreo GPU..."
echo "Timestamp,GPU Util %,VRAM Used MiB,Temperature" > /tmp/gpu_monitor.log

for i in {1..60}; do
    nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used,temperature.gpu --format=csv,noheader,nounits >> /tmp/gpu_monitor.log
    sleep 1
done

echo "✅ Monitoreo completado"