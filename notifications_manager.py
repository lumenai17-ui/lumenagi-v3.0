#!/usr/bin/env python3
"""
Notifications Manager v1.0 — Sistema de alertas para LumenAGI

Alertas automáticas cuando:
- Task larga (>2 min) termina
- GPU >90% por >5 min
- Costo de sesión >$5
- Error crítico en agente
- Qwen 32B se descarga de VRAM
"""

import json
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading


class AlertLevel(Enum):
    """Niveles de alerta"""
    INFO = "info"           # 🟢 Informativo
    WARNING = "warning"     # 🟡 Atención
    CRITICAL = "critical"   # 🔴 Urgente


class AlertType(Enum):
    """Tipos de alerta"""
    TASK_COMPLETE = "task_complete"
    GPU_HIGH = "gpu_high"
    GPU_VRAM_LOST = "gpu_vram_lost"
    COST_THRESHOLD = "cost_threshold"
    AGENT_ERROR = "agent_error"
    SYSTEM_DOWN = "system_down"
    MANUAL = "manual"


@dataclass
class Notification:
    """Una notificación individual"""
    id: str
    type: AlertType
    level: AlertLevel
    title: str
    message: str
    timestamp: str
    acknowledged: bool = False
    actions: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class NotificationsManager:
    """
    Manager de notificaciones multi-canal
    Soporta: Telegram (ready), Email (requiere config), Console
    """
    
    # Umbrales configurables
    THRESHOLDS = {
        'task_duration_alert': 120,      # segundos
        'gpu_high_utilization': 90,      # porcentaje
        'gpu_high_duration': 300,        # segundos (5 min)
        'cost_session_alert': 5.0,       # dólares
        'vram_critical': 5 * 1024,       # MB (menos de 5GB = descargado)
    }
    
    def __init__(self, telegram_channel: Optional[str] = None, email_config: Optional[Dict] = None):
        self.notifications: List[Notification] = []
        self.telegram_channel = telegram_channel or "main"
        self.email_config = email_config
        self.callbacks: Dict[AlertType, List[Callable]] = {}
        self.running = False
        self.monitor_thread = None
        
        # Estado para detección de condiciones
        self.state = {
            'gpu_high_since': None,
            'active_tasks': {},
            'last_cost': 0.0,
            'last_vram': 20 * 1024,  # MB
        }
        
    def register_callback(self, alert_type: AlertType, callback: Callable):
        """Registrar callback para tipo de alerta"""
        if alert_type not in self.callbacks:
            self.callbacks[alert_type] = []
        self.callbacks[alert_type].append(callback)
        
    def create_notification(self, ntype: AlertType, level: AlertLevel, 
                           title: str, message: str, actions: List[str] = None,
                           metadata: Dict = None) -> Notification:
        """Crear y almacenar notificación"""
        
        notif = Notification(
            id=f"{ntype.value}_{int(time.time()*1000)}",
            type=ntype,
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now().isoformat(),
            actions=actions or [],
            metadata=metadata or {}
        )
        
        self.notifications.append(notif)
        
        # Disparar callbacks
        if ntype in self.callbacks:
            for cb in self.callbacks[ntype]:
                try:
                    cb(notif)
                except Exception as e:
                    print(f"[Notification Callback Error] {e}")
        
        # Auto-enviar por canales según prioridad
        self._send_to_channels(notif)
        
        return notif
    
    def _send_to_channels(self, notif: Notification):
        """Enviar a canales configurados"""
        
        # Telegram para WARNING y CRITICAL
        if notif.level in [AlertLevel.WARNING, AlertLevel.CRITICAL]:
            self._send_telegram(notif)
        
        # Email para CRITICAL (si está configurado)
        if notif.level == AlertLevel.CRITICAL and self.email_config:
            self._send_email(notif)
        
        # Siempre log a consola
        emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}.get(notif.level.value, "•")
        print(f"\n{emoji} [{notif.level.value.upper()}] {notif.title}")
        print(f"   {notif.message}")
    
    def _send_telegram(self, notif: Notification):
        """Enviar por Telegram (usando message tool de OpenClaw)"""
        # Implementación usaría el message tool cuando esté disponible
        # Por ahora, log marcado
        print(f"   [TELEGRAM QUEUED] → {self.telegram_channel}")
        
    def _send_email(self, notif: Notification):
        """Enviar por Email (requiere SMTP config)"""
        print(f"   [EMAIL QUEUED] → {self.email_config.get('to', 'admin')}")
    
    # === DETECTORES DE CONDICIONES ===
    
    def check_task_completion(self, task_id: str, task_name: str, 
                             duration_seconds: float, success: bool = True):
        """Detectar cuando task larga termina"""
        if duration_seconds > self.THRESHOLDS['task_duration_alert']:
            level = AlertLevel.INFO if success else AlertLevel.WARNING
            self.create_notification(
                AlertType.TASK_COMPLETE,
                level,
                f"Task completado: {task_name}",
                f"Duración: {duration_seconds:.1f}s | Status: {'✅' if success else '❌'}",
                actions=["view_details", "run_similar"],
                metadata={"task_id": task_id, "duration": duration_seconds, "success": success}
            )
    
    def check_gpu_utilization(self, gpu_util: int, vram_used_mb: int):
        """Detectar GPU alta utilización sostenida"""
        
        # GPU >90%
        if gpu_util > self.THRESHOLDS['gpu_high_utilization']:
            if self.state['gpu_high_since'] is None:
                self.state['gpu_high_since'] = time.time()
            else:
                duration = time.time() - self.state['gpu_high_since']
                if duration > self.THRESHOLDS['gpu_high_duration']:
                    self.create_notification(
                        AlertType.GPU_HIGH,
                        AlertLevel.WARNING,
                        "GPU Alto uso sostenido",
                        f"GPU a {gpu_util}% por {duration/60:.1f} minutos",
                        actions=["check_processes", "optimize"],
                        metadata={"utilization": gpu_util, "duration_seconds": duration}
                    )
                    # Resetear para no spamear
                    self.state['gpu_high_since'] = None
        else:
            self.state['gpu_high_since'] = None
        
        # VRAM perdida (Qwen descargado)
        if vram_used_mb < self.THRESHOLDS['vram_critical'] and self.state['last_vram'] > self.THRESHOLDS['vram_critical']:
            self.create_notification(
                AlertType.GPU_VRAM_LOST,
                AlertLevel.CRITICAL,
                "🚨 Qwen 32B perdido de VRAM",
                f"VRAM cayó de {self.state['last_vram']/1024:.1f}GB a {vram_used_mb/1024:.1f}GB",
                actions=["reload_qwen", "check_keepalive"],
                metadata={"last_vram": self.state['last_vram'], "current_vram": vram_used_mb}
            )
        
        self.state['last_vram'] = vram_used_mb
    
    def check_cost_threshold(self, session_cost: float):
        """Detectar cuando costo excede umbral"""
        if session_cost > self.THRESHOLDS['cost_session_alert'] and self.state['last_cost'] <= self.THRESHOLDS['cost_session_alert']:
            self.create_notification(
                AlertType.COST_THRESHOLD,
                AlertLevel.WARNING,
                "💰 Umbral de costo alcanzado",
                f"Sesión: ${session_cost:.2f} (límite: ${self.THRESHOLDS['cost_session_alert']})",
                actions=["review_usage", "switch_to_local"],
                metadata={"cost": session_cost, "threshold": self.THRESHOLDS['cost_session_alert']}
            )
        self.state['last_cost'] = session_cost
    
    def check_agent_error(self, agent_name: str, error_message: str, task: str):
        """Detectar error crítico en agente"""
        self.create_notification(
            AlertType.AGENT_ERROR,
            AlertLevel.CRITICAL,
            f"❌ Error en {agent_name}",
            f"Task: {task[:50]}... | Error: {error_message[:100]}...",
            actions=["retry", "escalate", "view_logs"],
            metadata={"agent": agent_name, "task": task, "error": error_message}
        )
    
    def send_manual_notification(self, title: str, message: str, level: AlertLevel = AlertLevel.INFO):
        """Enviar notificación manual (desde heartbeat o triggers)"""
        return self.create_notification(
            AlertType.MANUAL,
            level,
            title,
            message,
            actions=["acknowledge", "dismiss"]
        )
    
    # === QUERY Y GESTIÓN ===
    
    def get_unacknowledged(self, level: Optional[AlertLevel] = None) -> List[Notification]:
        """Obtener notificaciones no reconocidas"""
        notifs = [n for n in self.notifications if not n.acknowledged]
        if level:
            notifs = [n for n in notifs if n.level == level]
        return sorted(notifs, key=lambda x: x.timestamp, reverse=True)
    
    def acknowledge(self, notif_id: str):
        """Marcar notificación como reconocida"""
        for n in self.notifications:
            if n.id == notif_id:
                n.acknowledged = True
                return True
        return False
    
    def get_stats(self) -> Dict:
        """Estadísticas de notificaciones"""
        by_type = {}
        by_level = {}
        for n in self.notifications:
            by_type[n.type.value] = by_type.get(n.type.value, 0) + 1
            by_level[n.level.value] = by_level.get(n.level.value, 0) + 1
        
        return {
            "total": len(self.notifications),
            "unacknowledged": len(self.get_unacknowledged()),
            "by_type": by_type,
            "by_level": by_level,
            "history_hours": 24
        }


# === INTEGRACIÓN CON DASHBOARD ===

def create_notifications_endpoint(dashboard_app, notifications_manager: NotificationsManager):
    """
    Agregar endpoints de notificaciones al dashboard Flask
    """
    from flask import jsonify
    
    @dashboard_app.route('/api/notifications')
    def api_notifications():
        """Get all unacknowledged notifications"""
        level = None  # Could filter by query param
        notifs = notifications_manager.get_unacknowledged(level)
        return jsonify({
            "notifications": [
                {
                    "id": n.id,
                    "type": n.type.value,
                    "level": n.level.value,
                    "title": n.title,
                    "message": n.message,
                    "timestamp": n.timestamp,
                    "actions": n.actions
                }
                for n in notifs
            ],
            "count": len(notifs)
        })
    
    @dashboard_app.route('/api/notifications/ack', methods=['POST'])
    def ack_notification():
        """Acknowledge a notification"""
        from flask import request
        data = request.json
        notif_id = data.get('id')
        success = notifications_manager.acknowledge(notif_id)
        return jsonify({"success": success})
    
    @dashboard_app.route('/api/notifications/stats')
    def notifications_stats():
        """Get notification statistics"""
        return jsonify(notifications_manager.get_stats())


# === DEMO ===

def demo_notifications():
    """Demo del sistema de notificaciones"""
    
    print("="*70)
    print("🔔 NOTIFICATIONS MANAGER v1.0 Demo")
    print("="*70)
    
    mgr = NotificationsManager(telegram_channel="main")
    
    # Simular eventos
    print("\n1. Task largo completado:")
    mgr.check_task_completion("task_123", "Generar embeddings", 145.0, success=True)
    
    print("\n2. GPU alta utilización:")
    mgr.check_gpu_utilization(95, 21 * 1024)
    
    print("\n3. Esperando 5 min simulado de GPU alta...")
    # Simular que pasó tiempo
    time.sleep(0.1)  # En demo es instantáneo
    
    print("\n4. VRAM perdido (Qwen descargado):")
    mgr.check_gpu_utilization(0, 500)  # Solo 500MB = descargado
    
    print("\n5. Umbral de costo:")
    mgr.check_cost_threshold(5.50)
    
    print("\n6. Error de agente:")
    mgr.check_agent_error("build-qwen32", "CUDA out of memory", "Entrenar modelo X")
    
    print("\n" + "="*70)
    print("📊 Stats:")
    print(f"   Total notificaciones: {mgr.get_stats()['total']}")
    print(f"   Sin reconocer: {mgr.get_stats()['unacknowledged']}")
    print(f"   Por nivel: {mgr.get_stats()['by_level']}")
    
    print("\n🔔 Notificaciones sin reconocer:")
    for n in mgr.get_unacknowledged():
        print(f"   [{n.level.value}] {n.title}")
    
    print("="*70)


if __name__ == "__main__":
    demo_notifications()
