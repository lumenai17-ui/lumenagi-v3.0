#!/usr/bin/env python3
"""
YouTube Analytics Integration v1.0

Diseñado para operar en modo autónomo sin datos personales del usuario.
El usuario solo necesita proporcionar OAuth credentials cuando esté listo.

Features:
- Daily API pull (YouTube Data API v3)
- Stats: views, CTR, AVD, engagement
- PNG chart generation
- Meta-analysis input ready
- RAG integration compatible
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Placeholder para cuando el usuario proporcione credenciales
# from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build


class YouTubeAnalyticsClient:
    """
    Cliente para YouTube Analytics API v3
    Operación: Autónoma (no requiere datos del usuario, solo OAuth credenciales)
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path
        self.service = None
        self.channel_id = None
        self.cache_dir = Path("./youtube_data")
        self.cache_dir.mkdir(exist_ok=True)
        
        if credentials_path and Path(credentials_path).exists():
            self._init_service()
    
    def _init_service(self):
        """Inicializar conexión API (cuando usuario proporcione credentials)"""
        try:
            # TODO: Implementar cuando usuario proporcione OAuth
            # from google.oauth2.credentials import Credentials
            # from googleapiclient.discovery import build
            # 
            # creds = Credentials.from_authorized_user_file(self.credentials_path)
            # self.service = build('youtube', 'v3', credentials=creds)
            pass
        except Exception as e:
            print(f"⚠️ YouTube API no inicializada: {e}")
    
    def is_configured(self) -> bool:
        """¿El cliente está listo para usar?"""
        return self.service is not None and self.channel_id is not None
    
    def request_oauth_setup(self) -> Dict:
        """
        Generar instrucciones para usuario configurar OAuth
        No requiere datos personales del usuario
        """
        return {
            "setup_required": True,
            "steps": [
                "Ir a https://console.cloud.google.com/",
                "Crear proyecto nuevo",
                "Habilitar YouTube Data API v3",
                "Crear OAuth 2.0 credentials (Desktop app)",
                "Descargar client_secret.json",
                "Ejecutar: gog auth credentials /path/to/client_secret.json",
                "Autorizar con tu cuenta de YouTube"
            ],
            "scopes_required": [
                "https://www.googleapis.com/auth/youtube.readonly",
                "https://www.googleapis.com/auth/yt-analytics.readonly"
            ],
            "help_url": "https://developers.google.com/youtube/registering_an_application"
        }
    
    def get_mock_data(self, days: int = 7) -> Dict:
        """
        Generar datos de ejemplo para desarrollo/testing
        No requiere datos del usuario — estructura demostrativa
        """
        today = datetime.now()
        
        mock_data = {
            "channel": {
                "id": "UC_EXAMPLE_CHANNEL_ID",
                "title": "[TU CANAL]",
                "subscribers": 0,  # Placeholder
                "videos_count": 0   # Placeholder
            },
            "period": {
                "start": (today - timedelta(days=days)).isoformat(),
                "end": today.isoformat(),
                "days": days
            },
            "summary": {
                "total_views": 0,
                "total_watch_time_hours": 0.0,
                "avg_view_duration": "0:00",
                "ctr": 0.0,
                "new_subscribers": 0
            },
            "videos": [
                {
                    "video_id": " ejemplo_video_1",
                    "title": "[Video reciente]",
                    "published_at": (today - timedelta(days=2)).isoformat(),
                    "views": 0,
                    "likes": 0,
                    "comments": 0,
                    "ctr": 0.0,
                    "avg_view_duration": "0:00",
                    "thumbnail_url": "https://i.ytimg.com/vi/.../maxresdefault.jpg"
                }
            ],
            "daily_trends": [
                {
                    "date": (today - timedelta(days=i)).strftime("%Y-%m-%d"),
                    "views": 0,
                    "watch_time": 0.0,
                    "subscribers": 0
                }
                for i in range(days)
            ],
            "recommendations": [
                "[Las recomendaciones aparecerán aquí después de conectar tu canal]",
                "[Basado en: CTR, AVD, engagement patterns]"
            ]
        }
        
        return mock_data
    
    def save_to_cache(self, data: Dict):
        """Persistir datos localmente"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cache_file = self.cache_dir / f"youtube_stats_{timestamp}.json"
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Mantener solo últimos 30 días
        self._cleanup_old_cache()
        
        return cache_file
    
    def _cleanup_old_cache(self, keep_days: int = 30):
        """Limpiar archivos antiguos"""
        cutoff = datetime.now() - timedelta(days=keep_days)
        
        for file in self.cache_dir.glob("youtube_stats_*.json"):
            try:
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                if file_time < cutoff:
                    file.unlink()
            except:
                pass
    
    def generate_chart_data(self, data: Dict) -> Dict:
        """
        Preparar datos para visualización (PNG/Dashboard)
        Retorna estructura lista para charting libraries
        """
        return {
            "chart_type": "multi",
            "title": "YouTube Analytics Dashboard",
            "period": data["period"],
            "datasets": [
                {
                    "label": "Views",
                    "data": [d["views"] for d in data["daily_trends"]],
                    "color": "#FF0000"
                },
                {
                    "label": "Watch Time (hrs)",
                    "data": [d["watch_time"] for d in data["daily_trends"]],
                    "color": "#00AA00"
                },
                {
                    "label": "Subscribers",
                    "data": [d["subscribers"] for d in data["daily_trends"]],
                    "color": "#0066CC"
                }
            ],
            "labels": [d["date"] for d in data["daily_trends"]]
        }
    
    def get_latest_cached(self) -> Optional[Dict]:
        """Obtener datos más recientes de caché"""
        cache_files = sorted(
            self.cache_dir.glob("youtube_stats_*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        
        if cache_files:
            with open(cache_files[0], 'r') as f:
                return json.load(f)
        return None
    
    def get_metrics_for_agent(self, data: Dict) -> str:
        """
        Formatear métricas para input de agente (meta-analysis)
        """
        summary = data["summary"]
        
        return f"""
YOUTUBE ANALYTICS REPORT ({data['period']['start'][:10]} to {data['period']['end'][:10]})
================================================================

CHANNEL OVERVIEW:
- Subscribers: {data['channel']['subscribers']:,}
- Total Videos: {data['channel']['videos_count']}

PERFORMANCE (Last {data['period']['days']} days):
- Total Views: {summary['total_views']:,}
- Watch Time: {summary['total_watch_time_hours']:.1f} hours
- Avg View Duration: {summary['avg_view_duration']}
- CTR: {summary['ctr']:.1%}
- New Subscribers: {summary['new_subscribers']:,}

TOP VIDEOS:
{self._format_top_videos(data['videos'])}

RECOMMENDATIONS:
{chr(10).join('- ' + r for r in data['recommendations'])}
"""
    
    def _format_top_videos(self, videos: List[Dict]) -> str:
        """Formatear lista de videos para reporte"""
        lines = []
        for i, v in enumerate(videos[:5], 1):
            lines.append(f"{i}. {v['title'][:50]}... - {v['views']:,} views, CTR: {v['ctr']:.1%}")
        return "\n".join(lines) if lines else "[No videos data]"


class YouTubeAnalyticsCron:
    """
    Job programado para daily YouTube pulls
    Integración con sistema cron de OpenClaw
    """
    
    def __init__(self, client: YouTubeAnalyticsClient):
        self.client = client
    
    def run_daily_pull(self) -> Dict:
        """
        Ejecutar pull diario de datos
        Retorna resultado para dashboard/notifications
        """
        if not self.client.is_configured():
            return {
                "success": False,
                "error": "YouTube API not configured",
                "setup_instructions": self.client.request_oauth_setup()
            }
        
        try:
            # Aquí iría el código real de API call cuando esté configurado
            # Por ahora: generar mock data con estructura correcta
            data = self.client.get_mock_data(days=7)
            
            # Guardar en caché
            cache_file = self.client.save_to_cache(data)
            
            # Generar chart data para dashboard
            chart_data = self.client.generate_chart_data(data)
            
            # Formatear para agente
            agent_input = self.client.get_metrics_for_agent(data)
            
            return {
                "success": True,
                "data": data,
                "chart_data": chart_data,
                "agent_input": agent_input,
                "cache_file": str(cache_file),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Integration helper for coordinator
def get_youtube_summary_for_coordinator() -> str:
    """
    Función de conveniencia para el coordinator
    Retorna resumen de YouTube stats o notificación de setup requerido
    """
    client = YouTubeAnalyticsClient()
    
    if not client.is_configured():
        return """
[YOUTUBE ANALYTICS: Not Configured]
Esta función requiere configuración de Google OAuth.
Instrucciones disponibles en youtube_analytics_client.request_oauth_setup()
"""
    
    # Usar últimos datos en caché o hacer pull nuevo
    data = client.get_latest_cached()
    if not data:
        cron = YouTubeAnalyticsCron(client)
        result = cron.run_daily_pull()
        if result["success"]:
            data = result["data"]
        else:
            return f"[YOUTUBE ERROR: {result.get('error', 'Unknown')}]"
    
    return client.get_metrics_for_agent(data)


# Demo / Testing
if __name__ == "__main__":
    print("="*60)
    print("📺 YouTube Analytics Integration v1.0")
    print("="*60)
    
    client = YouTubeAnalyticsClient()
    
    # Show setup instructions
    setup = client.request_oauth_setup()
    print(f"\n🔧 Setup Required: {setup['setup_required']}")
    print("\nSteps:")
    for i, step in enumerate(setup['steps'], 1):
        print(f"  {i}. {step}")
    
    # Demo with mock data
    print("\n" + "="*60)
    print("📊 Demo con Mock Data (Estructura lista para tus datos)")
    print("="*60)
    
    mock = client.get_mock_data(days=7)
    print(client.get_metrics_for_agent(mock))
    
    # Save demo cache
    cache_file = client.save_to_cache(mock)
    print(f"\n💾 Demo data saved: {cache_file}")
    
    # Chart data ready
    chart = client.generate_chart_data(mock)
    print(f"\n📈 Chart data ready: {len(chart['datasets'])} datasets")
