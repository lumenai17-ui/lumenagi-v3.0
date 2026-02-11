# Notifications System v1.0

Sistema de alertas automáticas para LumenAGI SWARM.

## Alertas Automáticas

| Condición | Nivel | Acción |
|-----------|-------|--------|
| Task >120s completa | ℹ️ INFO | Notificar tiempo y status |
| GPU >90% por >5min | ⚠️ WARNING | Alerta uso sostenido |
| VRAM <5GB (Qwen perdido) | 🚨 CRITICAL | Urgente: recargar modelo |
| Costo sesión >$5 | ⚠️ WARNING | Revisar gasto API |
| Error en agente | 🚨 CRITICAL | Notificar con detalles |
| Manual desde API | Configurable | Notificación custom |

## API Endpoints

```bash
# Obtener notificaciones pendientes
GET /api/notifications

# Reconocer notificación  
POST /api/notifications/ack
{"id": "task_complete_1234567890"}

# Estadísticas
GET /api/notifications/stats

# Crear notificación manual
POST /api/notify/manual
{
  "title": "Alerta personalizada",
  "message": "Algo importante pasó",
  "level": "warning"  # info | warning | critical
}
```

## WebSocket Events

```javascript
socket.on('metrics', (data) => {
  // data.notifications contiene count y últimas 5 notificaciones
  const notifs = data.notifications;
  // notifs.count, notifs.unread_critical, notifs.unread_warning
  // notifs.notifications[]
});

socket.on('notification_new', (notif) => {
  // Notificación en tiempo real
  // {id, level, title, message}
});

socket.on('agent_complete', (data) => {
  // Task completado con duración
  // {agent, task, duration}
});
```

## Integración con Dashboard

Las notificaciones se incluyen automáticamente en las métricas SocketIO:
- Revisión cada 5 segundos
- Métricas de GPU y costos monitoreadas
- Emisión inmediata cuando se detecta condición

## Uso en Código

```python
from notifications_manager import NotificationsManager

mgr = NotificationsManager()

# Task largo completado
mgr.check_task_completion("task_123", "Embedding", 145.0, success=True)

# GPU alta utilización
mgr.check_gpu_utilization(95, 21 * 1024)

# Umbral de costo
mgr.check_cost_threshold(5.50)

# Error
mgr.check_agent_error("build", "Out of memory", "Entrenar modelo")

# Manual
mgr.send_manual_notification("Listo", "Todo funcionando", AlertLevel.INFO)
```

## Archivos

- `notifications_manager.py` — Core del sistema
- `dashboard/v4/app_v4.4.py` — Dashboard con notificaciones

---
*Implementado: 2026-02-11 | Estado: ✅ Activo*
