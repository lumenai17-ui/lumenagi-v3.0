# Auto-Tool Selection Skill v1.0

Detección automática de herramientas necesarias para cada tarea.

## Uso

```python
from coordinator_swarm import SWARMCoordinator

coordinator = SWARMCoordinator(tool_plugin_enabled=True)
result = coordinator.run("Crea un script de backup")

# El coordinator ahora detecta automáticamente:
# - Tools necesarias (web_search, file_write, code_exec, etc.)
# - Agente óptimo (build-qwen32, research, create-qwen32)
# - Costo estimado antes de ejecutar
```

## Detección de Tools

| Patrón | Tool Detectada |
|--------|---------------|
| "investiga", "busca", "research" | `web_search` |
| "lee archivo", "extrae URL" | `web_fetch`, `file_read` |
| "crea script", "ejecuta" | `code_exec`, `file_write` |
| "genera imagen", "dibuja" | `image` |
| "avisar", "notificar Telegram" | `telegram` |
| "automatiza web", "login" | `browser` |
| "commit", "push", "git" | `github` |

## Integración

El plugin funciona en dos modos:

**Modo ENHANCED (default):**
- Detecta tools automáticamente
- Override de agente según tools
- Estimación de costo
- Fallback strategies

**Modo VANILLA:**
- Solo decision tree básico
- Sin detección de tools
- Compatible con v1.0

## Archivos

- `coordinator_swarm.py` — Coordinator principal v1.1
- `coordinator_tool_plugin.py` — Plugin de detección
- `coordinator_tool_selector.py` — Detector de patrones

## Ejemplo de Output

```
🧠 Coordinator [ENHANCED + TOOLS] recibió: Crea script de scraping...
📊 Análisis: research=False, code=True, review=False
🔧 Tools detectadas: ['file_write', 'code_exec']
💰 Costo estimado: FREE (Qwen 32B local)
📋 Plan creado: 1 tareas
   - T1: build [tools: ['file_write', 'code_exec']]
```

---
*Implementado: 2026-02-11 | Estado: ✅ Activo*
