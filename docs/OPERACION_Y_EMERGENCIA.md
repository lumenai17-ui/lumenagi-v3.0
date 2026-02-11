# Procedimientos de Operación y Emergencia
## LumenAGI SWARM v3.0

---

## 🔄 PROCESO ADECUADO: Cierre y Arranque Controlado

### CIERRE CONTROLADO (Graceful Shutdown)

```bash
# === PASO 1: Detener Dashboard ===
pkill -f "app_v4.3.py"  # o el proceso de Flask que esté corriendo
echo "Dashboard detenido"

# === PASO 2: Verificar estado de VRAM ===
ollama ps
# NOTA: Qwen 32B persistirá mientras no hagas shutdown del WSL

# === PASO 3: Sync final de datos ===
cd /home/lumen/.openclaw/workspace
python integrations/notion_sync.py --sync 2>/dev/null || echo "Notion no configurado"

# === PASO 4: Backup de memoria diaria ===
cp memory/2026-02-11.md memory/2026-02-11-backup-$(date +%H%M).md

# === PASO 5: Commit a GitHub (si hay cambios) ===
cd /home/lumen/lumenagi-v3.0
git add -A
git commit -m "Pre-shutdown checkpoint $(date '+%H:%M')" 2>/dev/null || true

# === PASO 6: Verificar cron jobs activos ===
crontab -l | grep keepalive  # Debería mostrar el keep-alive

# === PASO 7: Shutdown ===
sudo shutdown -h now  # o simplemente cierra WSL: wsl --shutdown
```

### ARRANQUE CONTROLADO

```bash
# === PASO 1: Iniciar WSL ===
wsl  # o abrir terminal WSL

# === PASO 2: Verificar OpenClaw Gateway ===
openclaw health
# Si no responde:
# openclaw gateway start

# === PASO 3: Verificar/cargar Qwen 32B ===
ollama ps
# Si no está cargado:
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5:32b","prompt":"load","keep_alive":"48h"}'

# === PASO 4: Reactivar Keep-Alive (si es necesario) ===
# El cron debería estar activo, verificar:
crontab -l | grep qwen32b
# Si no está, reinstalar:
# */3 * * * * /home/lumen/.openclaw/scripts/keepalive-qwen32b.sh

# === PASO 5: Iniciar Dashboard ===
cd /home/lumen/.openclaw/workspace/dashboard/v4
python app_v4.3.py &
sleep 2
echo "Dashboard en http://127.0.0.1:8766/"

# === PASO 6: Verificar Telegram ===
openclaw message --channel telegram --action send --message "🤖 Lumen reiniciado - $(date '+%H:%M')"

# === PASO 7: Sync Notion (si configurado) ===
python /home/lumen/.openclaw/workspace/integrations/notion_sync.py --sync 2>/dev/null || true
```

---

## ⚡ PROCESO DE EMERGENCIA: Falla de Energía/Batería

### ESTADO DESPUÉS DE FALLA DE ENERGÍA

| Componente | Estado | Acción Requerida |
|------------|--------|------------------|
| **Qwen 32B** | ❌ **PERDIDO** | Recargar en VRAM |
| **Keep-Alive** | ❌ **DETENIDO** | Reactivar cron |
| **Dashboard** | ❌ **CERRADO** | Reiniciar |
| **OpenClaw Gateway** | ✅ **Persiste** (systemd/WSL) | Verificar |
| **Telegram Pairing** | ✅ **Persiste en config** | Verificar |
| **GitHub Repo** | ✅ **Seguro** | Pull si es necesario |
| **Notion Config** | ✅ **Seguro en disco** | Verificar sync |

### RECUPERACIÓN POST-CAÍDA

```bash
# === PASO 1: Assess Damage ===
echo "=== Estado del sistema post-caída ==="

# Verificar Ollama
ollama ps
echo "⚠️ Si está vacío -> Qwen 32B se perdió, recargar"

# Verificar Gateway
openclaw health || echo "❌ Gateway caído"

# Verificar Dashboard
lsof -i :8766 || echo "❌ Dashboard caído"

# === PASO 2: Recuperación Automática ===

# Recargar Qwen 32B (crítico)
echo "🔄 Recargando Qwen 32B..."
curl -s -X POST http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5:32b","prompt":"Hello","stream":false,"keep_alive":"48h"}' | jq -r '.done'

# Verificar VRAM
nvidia-smi | grep -E "Qwen|MiB"

# === PASO 3: Reiniciar Dashboard ===
echo "🔄 Reiniciando Dashboard..."
pkill -f app_v4.3.py 2>/dev/null
cd /home/lumen/.openclaw/workspace/dashboard/v4
nohup python app_v4.3.py > /tmp/dashboard.log 2>&1 &
sleep 3
curl -s http://127.0.0.1:8766/ > /dev/null && echo "✅ Dashboard OK" || echo "❌ Dashboard FAIL"

# === PASO 4: Verificar/Reactivar Keep-Alive ===

# Ver si el script existe
ls -la /home/lumen/.openclaw/scripts/keepalive-qwen32b.sh

# Ver cron
crontab -l | grep keepalive

# Si no está el cron, reinstalar:
# (crontab -l 2>/dev/null; echo "*/3 * * * * /home/lumen/.openclaw/scripts/keepalive-qwen32b.sh") | crontab -

# Ejecutar manualmente una vez para asegurar:
/home/lumen/.openclaw/scripts/keepalive-qwen32b.sh
echo "✅ Keep-alive forzado"

# === PASO 5: Verificación Final ===
echo ""
echo "=== CHECKLIST POST-REINICIO ==="
echo "[ ] Gateway: $(openclaw health 2>&1 | head -1)"
echo "[ ] Qwen 32B: $(ollama ps 2>/dev/null | grep qwen | wc -l) modelo(s) cargado(s)"
echo "[ ] Dashboard: $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8766/) HTTP status"
echo "[ ] Keep-Alive: $(crontab -l 2>/dev/null | grep -c qwen32b) job(s) active(s)"
echo "[ ] VRAM: $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1) MB usado"
echo "[ ] Telegram: Pendiente verificación manual"
```

### AUTOMATIZACIÓN: Script de Recuperación

**Crear `~/recovery.sh`:**

```bash
#!/bin/bash
# LumenAGI Emergency Recovery Script
# Ejecutar después de falla de energía

set -e

LOG_FILE="/tmp/lumen_recovery_$(date +%Y%m%d_%H%M%S).log"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

echo "🚨 RECOVERY INICIADO: $(date)"

# 1. Gateway
if ! openclaw health >/dev/null 2>&1; then
    echo "❌ Gateway caído, requiere: openclaw gateway start"
else
    echo "✅ Gateway activo"
fi

# 2. Qwen 32B
if ! curl -s http://localhost:11434/api/ps | grep -q qwen; then
    echo "🔄 Recargando Qwen 32B..."
    curl -s -X POST http://localhost:11434/api/generate \
      -d '{"model":"qwen2.5:32b","prompt":"load","stream":false,"keep_alive":"48h"}' > /dev/null
    sleep 30  # Esperar carga
    echo "✅ Qwen 32B recargado"
else
    echo "✅ Qwen 32B ya estaba cargado"
fi

# 3. Forzar keep-alive
/home/lumen/.openclaw/scripts/keepalive-qwen32b.sh
echo "✅ Keep-alive ejecutado"

# 4. Dashboard
if ! lsof -i :8766 >/dev/null 2>&1; then
    echo "🔄 Iniciando Dashboard..."
    cd /home/lumen/.openclaw/workspace/dashboard/v4
    nohup python app_v4.3.py > /tmp/dashboard.log 2>&1 &
    sleep 2
    echo "✅ Dashboard iniciado"
else
    echo "✅ Dashboard ya activo"
fi

# 5. Notion sync (si aplica)
if [ -f /home/lumen/.openclaw/workspace/secrets/notion_credentials.json ]; then
    python /home/lumen/.openclaw/workspace/integrations/notion_sync.py --sync || true
    echo "✅ Notion sync intentado"
fi

echo ""
echo "🎯 RECOVERY COMPLETADO: $(date)"
echo "Log guardado en: $LOG_FILE"
echo ""
echo "Próximos pasos:"
echo "1. Verificar Telegram: openclaw message --channel telegram --action send --message 'test'"
echo "2. Abrir Dashboard: http://127.0.0.1:8766/"
echo "3. Verificar Qwen: ollama ps"
```

**Hacer ejecutable:**
```bash
chmod +x ~/recovery.sh
```

---

## 📋 CHECKLIST RÁPIDO

### Antes de Cerrar (Siempre)
- [ ] Dashboard detenido: `pkill -f app_v4.3.py`
- [ ] Git commit si hay cambios
- [ ] Ollama ps (verificar que Qwen esté) — **no requiere acción, VRAM se mantiene mientras WSL corre**
- [ ] Nota sobre estado actual en memory

### Después de Encender (Siempre)
- [ ] `openclaw health`
- [ ] `ollama ps` — si vacío, recargar Qwen
- [ ] `crontab -l | grep qwen32b` — verificar keep-alive
- [ ] `curl http://127.0.0.1:8766/` — verificar/dashboard
- [ ] Probar Telegram
- [ ] Notion sync si está configurado

### Después de Falla de Energía
- [ ] Ejecutar `~/recovery.sh`
- [ ] Verificar VRAM: `nvidia-smi`
- [ ] Esperar 1-2 minutos para carga completa de Qwen
- [ ] Test end-to-end: mensaje → respuesta

---

## ⚠️ Puntos Críticos

### Lo que se PIERDE en caída:
1. **Interacciones sin guardar** — no hay autosave en conversaciones
2. **Unsaved work** — archivos no commiteados
3. **Qwen 32B en VRAM** — TARDE ~2-3 min en recargar
4. **Dashboard state** — traces se reinician

### Lo que PERSISTE:
1. **GitHub repo** — todo commiteado está seguro
2. **Archivos de config** — OpenClaw config, cron jobs
3. **Telegram pairing** — guardado en config
4. **Notion credentials** — archivo en disco

---

## 🔧 Comandos Útiles de Diagnóstico

```bash
# Estado completo del sistema
alias lumen-status='echo "=== LumenAGI Status ===" && ollama ps && echo "" && openclaw health && echo "" && nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader && echo "" && curl -s http://127.0.0.1:8766/ >/dev/null && echo "Dashboard: OK" || echo "Dashboard: DOWN"'

# Quick recovery
alias lumen-recover='~/recovery.sh'

# Forzar keep-alive ahora
alias lumen-ping='/home/lumen/.openclaw/scripts/keepalive-qwen32b.sh && echo "Ping enviado"'

# Ver últimos errores
alias lumen-logs='tail -50 /tmp/dashboard.log 2>/dev/null || echo "No hay logs"'
```

Añadir a `~/.bashrc` para disponibilidad permanente.

---

*Documento creado: 2026-02-11 | Versión 1.0*
