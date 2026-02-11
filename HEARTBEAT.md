# HEARTBEAT.md — Checks Periódicos

## Cada 30 min, rotar entre:

### Check 1: Sistema
- [ ] Gateway alive? (`openclaw health`)
- [ ] Memory status OK?
- Reportar si algo está down

### Check 2: Comunicación
- [ ] Telegram pendientes?
- [ ] Algo importante que reportar?
- Notificar si hay urgente

### Check 3: Proactividad
- [ ] Tareas pendientes en archivo?
- [ ] Algo que puedo avanzar solo?
- Ejecutar sin preguntar

### Check 4: Moltbook (cada 30 min)
- [ ] Feed check (API: `curl "https://www.moltbook.com/api/v1/feed?sort=new&limit=5" -H "Authorization: Bearer $KEY"`)
- [ ] Comment en posts relevantes (máx 1-2 por check)
- [ ] Upvote contenido valioso
- [ ] Si hay algo interesante, reportar a Humberto

---

## Tracking
Estado en: `memory/heartbeat-state.json`

## Output
- Si todo OK: `HEARTBEAT_OK`
- Si hay acción: ejecutar y reportar
- No spam entre 23:00-08:00
