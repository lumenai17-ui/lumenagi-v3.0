# Fase 3: Ideas Según Nuestras Tareas Actuales

## Estado Actual (v4.5)
- Dashboard completo: GPU, CPU, RAM, Token/Cost tracking, Task Manager
- SWARM: Kimi + Qwen 32B local + GPT-4o
- Keep-alive estable
- GitHub repo documentado

## 🎯 Tareas Pendientes Principales

### 1. 🔌 Integración Notion API (🔄 EN PROGRESO)
**Contexto**: Dashboard tiene sección "Tus Tareas (Hb)" pero está vacía/sincronizando

**Implementación**:
- ✅ Cliente Python (`notion_client.py`)
- ✅ Sincronizador con CLI (`notion_sync.py`)
- ✅ Backend endpoint (`/data/notion_tasks.json`)
- ✅ Frontend integrado (`index_v4.5.html`)
- ⏳ OAuth setup en https://www.notion.so/my-integrations
- ⏳ Database compartida y ID capturado

**Archivos**:
- `integrations/notion_client.py` — Cliente API completo
- `integrations/notion_sync.py` — Sync + setup wizard
- `skills/NOTION_INTEGRATION.md` — Documentación

**Setup requerido**:
```bash
export NOTION_TOKEN="secret_xxxxx"
export NOTION_DATABASE_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
python integrations/notion_sync.py --sync
```

---

### 2. 🦾 RAG Integration en Coordinator
**Contexto**: Memory system con ChromaDB implementado, no integrado

**Implementación**:
- Antes de cada tarea: query RAG para skills relevantes
- Coordinator recibe contexto adicional automático
- Cache de skills usados frecuentemente

**Valor**: Agentes con "conocimiento institucional" de nuestros propios skills

---

### 3. 🎛️ Auto-Tool Selection
**Contexto**: Coordinator decide qué agente usar, pero no qué tools

**Implementación**:
- Clasificador: ¿necesita GPU? ¿necesita web? ¿necesita código?
- Selección automática de tools según task
- Fallback graceful si tool falla

**Valor**: Menos intervención manual, más autonomía

---

### 4. 🧠 Agent Memory Persistence
**Contexto**: Cada sesión empieza de cero

**Implementación**:
- Resumen de contexto anterior al inicio
- "Working memory" por agente
- Checkpoint de estado cada 10 min

**Valor**: Continuidad entre conversaciones

---

### 5. 🔔 Multi-Channel Notifications
**Contexto**: Solo Telegram configurado

**Implementación**:
- Notifications cuando task larga termina
- Alertas si GPU > 90% por >10 min
- Daily digest de actividad

**Canales**: Telegram (✅), Email (⚠️), Discord (opcional)

---

### 6. ⚡ Workflow Templates
**Contexto**: Tareas recurrentes sin estandarizar

**Implementación**:
- Plantillas JSON: "investigar → draft → revisar → publicar"
- Workflow "deploy": code → test → commit → push
- Workflow "content": research → write → SEO → post

**Valor**: 1 comando ejecuta flujo completo

---

### 7. 📊 Dashboard Widgets Dinámicos
**Contexto**: Dashboard v4.5 tiene layout fijo

**Implementación**:
- Drag & drop widgets
- Widgets configurables (¿quieres CPU aquí o allá?)
- Themes (dark/light/navy)
- Fullscreen mode para presentaciones

---

### 8. 🎓 Self-Improvement Loop
**Contexto**: Decisiones de routing no se aprenden

**Implementación**:
- Log de decisiones: task → agent elegido → resultado
- Análisis semanal: ¿acertamos el routing?
- Ajuste automático de pesos
- Reporte: "Esta semana Qwen fue mejor que GPT-4o en X tipo de tareas"

---

### 9. 🔗 External Integrations Wishlist
- GitHub: auto-PR cuando completamos feature
- Calendar: schedule tasks para horario óptimo
- Weather: reminders contextuales (?)
- Spotify: música para focus time (opcional!)

---

### 10. 🦥 Lazy Loading de Modelos
**Contexto**: Qwen 32B siempre en VRAM (20GB usado)

**Implementación**:
- Predicción: ¿se usará en los próximos 15 min?
- Si no: unload automático
- Si sí: keep-alive optimizado (no cada 3 min, cada 5 min si hay actividad)

**Valor**: Liberar VRAM para FLUX/SVD cuando no se usa Qwen

---

## 🎯 Mi Recomendación de Prioridad

**Esta semana**:
1. Notion API (bloquea Task Manager)
2. RAG en Coordinator (mejora calidad de tareas)

**Siguiente semana**:
3. Auto-tool selection
4. Notifications para tasks largas

**Después**:
5. Workflow templates
6. Agent memory persistence

---

¿Cuál te interesa más? Puedo empezar con Notion API + RAG en paralelo.
