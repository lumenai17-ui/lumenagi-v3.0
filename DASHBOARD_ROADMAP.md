# Dashboard Evolution Roadmap

Tracking all system features for future dashboard integration.

## Current Dashboard v4.5 Components

### ✅ Implemented
- [x] GPU/VRAM real-time monitoring
- [x] CPU/RAM/Disk system stats  
- [x] Token tracking (Kimi/Qwen/GPT-4o)
- [x] Cost estimation display
- [x] SWARM topology visualization
- [x] Real-time traces panel
- [x] GPU history chart
- [x] Notion tasks integration (backend ready)
- [x] Mobile version v1.0 (emulated data)

---

## Phase 3 Features (Fase 3) — Pending Dashboard Integration

### 1. Auto-Tool Selection ✅ IMPLEMENTED
**Files:** `coordinator_tool_plugin.py`, `coordinator_tool_selector.py`  
**Function:** Detects tools needed per task automatically  
**Dashboard Need:** Show "detected tools" in real-time, tool usage stats  
**Widget Idea:** Tool detection panel — shows what tools the coordinator detected for current task

### 2. Notifications System ⏳ PENDING
**Scope:** Alert when long task completes, GPU >90%, errors  
**Channels:** Telegram (ready), Email (needs credentials), Discord (optional)  
**Dashboard Need:** Notification center with history, alert settings  
**Widget Idea:** Notification bell with unread count, alert history table

### 3. RAG Memory Integration ⏳ PENDING  
**Files:** `memory_system.py` (ChromaDB + nomic-embed-text)  
**Function:** Coordinator queries past conversations/skills before answering  
**Dashboard Need:** Show memory hits, relevance scores, stored context  
**Widget Idea:** Memory activity graph, recent memories panel, search interface

### 4. Agent Activity Logs ⏳ PENDING
**Current:** Basic traces in dashboard  
**Need:** Detailed per-agent metrics (tokens/min, success rate, latency)  
**Widget Idea:** Agent performance cards, comparative efficiency chart

### 5. Workflow Templates ⏳ PENDING
**Concept:** "Deploy: code→test→commit→push" or "Content: research→write→post"  
**Dashboard Need:** Workflow runner UI, template selection, progress tracking  
**Widget Idea:** Workflow launcher, active workflows status, template library  

---

## Dashboard Architecture Notes

### Backend (`app_v4.x.py`)
```python
# Current: SocketIO emits metrics every 1s
# Future additions:
- Tool detection events from coordinator
- Notification queue integration  
- RAG query metrics from memory_system
- Agent activity detailed logs
- Workflow execution state
```

### Frontend (`index_v4.x.html` + `index_mobile.html`)
```javascript
// Current: Receives 'metrics' event
// Future additions:
- 'tool_detected' event handler
- 'notification' event handler
- 'rag_query' event handler  
- 'workflow_update' event handler
```

### Data Flow
```
Coordinator Tool Plugin → WebSocket → Dashboard
  └── tool_detected: {task, tools[], confidence}

Memory System RAG → WebSocket → Dashboard  
  └── rag_query: {query, results[], latency_ms}

Notification Manager → WebSocket → Dashboard
  └── notification: {type, message, priority, timestamp}

Workflow Engine → WebSocket → Dashboard
  └── workflow_update: {id, step, progress%, status}
```

---

## Planned Widgets

| Widget | Purpose | Backend Endpoint |
|--------|---------|------------------|
| Tool Detection Panel | Show active tools per task | `/api/tools/active` |
| Notification Center | Alert history & settings | `/api/notifications` |
| Memory Activity | RAG queries & hits | `/api/memory/activity` |
| Agent Performance | Tokens/speed per agent | `/api/agents/metrics` |
| Workflow Runner | Template execution UI | `/api/workflows` |
| Cost Projections | Estimated vs actual spend | `/api/costs/projected` |

---

## Mobile Dashboard v2.0 Wishlist

- [ ] Real data from SocketIO (not emulated)
- [ ] Tool detection badges
- [ ] Swipe notifications  
- [ ] Quick action buttons (emergency stop, pause)
- [ ] Dark/light theme toggle
- [ ] Offline mode (cached last state)

---

## Integration Checklist

When implementing each feature:
- [ ] Backend emits WebSocket events
- [ ] Frontend receives and displays
- [ ] Mobile version updated
- [ ] Skill documentation created
- [ ] Added to this roadmap

---

*Last updated: 2026-02-11 17:40 EST*  
*Status: Tracking for Dashboard v5.0 planning*
