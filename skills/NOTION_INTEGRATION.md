# Notion Integration Skill

Integración completa de Notion API con LumenAGI Dashboard para sincronización de tareas.

## Archivos

- `integrations/notion_client.py` — Cliente Python para Notion API
- `integrations/notion_sync.py` — Sincronizador + setup wizard
- `dashboard/v4/app_v4.3.py` — Backend con endpoint Notion
- `dashboard/v4/index_v4.5.html` — Frontend renderizando tareas

## Setup

### 1. Crear integración en Notion

1. Ve a: https://www.notion.so/my-integrations
2. Click "New integration"
3. Nombre: "LumenAGI"
4. Selecciona tu workspace
5. Copia el token (empieza con `secret_`)

### 2. Compartir database

1. Ve a tu database de tareas en Notion
2. Menu "..." → "Add connections"
3. Selecciona "LumenAGI"
4. Copia el database ID de la URL:
   - `https://www.notion.so/workspace/12345678-1234-1234-1234-123456789abc?v=...`
   - ID = `12345678-1234-1234-1234-123456789abc`

### 3. Configurar credenciales

```bash
export NOTION_TOKEN="secret_xxxxx"
export NOTION_DATABASE_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

Para persistencia, añadir a `~/.bashrc` o crear archivo en `secrets/notion_credentials.json`:

```json
{
  "token": "secret_xxxxx",
  "database_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### 4. Probar conexión

```bash
cd /home/lumen/.openclaw/workspace/integrations
python notion_sync.py --setup
```

### 5. Sincronizar manualmente

```bash
python notion_sync.py --sync
```

## Campos soportados

El parser detecta automáticamente campos con estos nombres:

| Campo | Nombres detectados |
|-------|-------------------|
| Título | Name, Title, Task, Tarea |
| Status | Status, Estado, State |
| Prioridad | Priority, Prioridad, Importance |
| Due date | Due date, Fecha, Deadline, Vencimiento |
| Tags | Tags, Etiquetas, Category, Categoría |

## API del cliente

```python
from notion_client import NotionClient

client = NotionClient(token)
tasks = client.get_tasks(database_id)

for task in tasks:
    print(f"{task.title} [{task.status}] - {task.priority}")
```

## Dashboard integration

- Tareas aparecen en panel derecho "Tus Tareas (Hb)"
- Orden: In Progress → Not Started → Done
- Indicador visual: ● En progreso / ○ Pendiente / ✓ Completado
- Prioridad alta marcada con punto rojo

## Cron job (auto-sync)

Ejecuta cada 5 minutos:

```bash
# Añadir a crontab -e
*/5 * * * * cd /home/lumen/.openclaw/workspace && python integrations/notion_sync.py --sync >> logs/notion_sync.log 2>&1
```

## Troubleshooting

| Problema | Solución |
|----------|----------|
| "NOTION_TOKEN no configurado" | Setear variable de entorno o secrets file |
| "database not found" | Verificar permisos de conexión en Notion |
| No aparecen tareas | Verificar que el database tiene campo "Status" |
| Rate limit | Notion limita a 3 requests/segundo, esperar |
