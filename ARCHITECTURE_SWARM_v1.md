# 🏗️ LumenAGI SWARM Architecture v1.0
## Híbrido: Qwen 32B Local + APIs Cloud (Approved)

---

## 📋 Resumen Ejecutivo

| Componente | Ubicación | VRAM/Costo | Cuándo usar |
|------------|-----------|------------|-------------|
| **Coordinator** | Qwen 32B Local | 20GB VRAM | Siempre activo |
| **Router Agent** | Qwen 32B Local | (comparte) | Clasificación de tareas |
| **Parser/Formatter** | Qwen 32B Local | (comparte) | JSON, estructuras |
| **Simple Planner** | Qwen 32B Local | (comparte) | Task decomposition básico |
| **Boilerplate Code** | Qwen 32B Local | (comparte) | Utilidades, scripts simples |
| **Complex Reasoning** | Pony-Alpha / Aurora Alpha | API $ | Razonamiento profundo |
| **Code Review** | Claude Sonnet | API $ | Debug, optimización |
| **Research Synthesis** | Claude Sonnet | API $ | Análisis complejo |
| **Image Generation** | FLUX.1-schnell | Local GPU restante | Imágenes |

---

## 🎯 Principios de Diseño

1. **"Fast Path" Local**: 80% de decisiones simples se resuelven local (velocidad, costo cero)
2. **"Smart Path" Cloud**: 20% crítico va a APIs (calidad máxima)
3. **Auto-Routing**: El Coordinator decide automáticamente sin intervención humana
4. **Una fuente de verdad**: Todo pasa por el Coordinator Qwen 32B

---

## 🔄 Flujo de Trabajo (User Request)

```
┌─────────────────────────────────────────────────────────────┐
│  USUARIO: "Crea un agente que analice emails y genere resumen" │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  COORDINATOR (Qwen 32B)                                      │
│  • Analiza la request                                          │
│  • Descompone en sub-tareas                                    │
│  • Asigna agents                                               │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌────────┐  ┌────────┐  ┌──────────┐
   │Router  │  │Planner │  │If complex│
   │Local   │  │Local   │  │-> Cloud  │
   └────┬───┘  └────┬───┘  └────┬─────┘
        │           │          │
        ▼           ▼          ▼
┌─────────────────────────────────────────────────────────────┐
│  A. "Code simple" → Qwen 32B (local)                       │
│     • Generar boilerplate                                     │
│     • Estructurar JSON config                               │
│     • Crear prompts base                                      │
├─────────────────────────────────────────────────────────────┤
│  B. "Complex reasoning" → Claude/Pony (cloud)              │
│     • Diseño de arquitectura                                  │
│     • Decisiones arquitectónicas                              │
│     • Edge cases complejos                                    │
├─────────────────────────────────────────────────────────────┤
│  C. "Research" → Cloud APIs                                  │
│     • Buscar best practices actuales                          │
│     • Syntheis de información                                 │
└────────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PARSER (Qwen 32B)                                           │
│  • Combina outputs                                            │
│  • Estructura respuesta final                                 │
│  • Formato consistente                                        │
└────────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
                    USUARIO
```

---

## 🤖 Agentes Locales (Qwen 32B)

### 1. Coordinator Agent
**Rol**: Orquestador principal, punto de entrada único
**Input**: User request
**Output**: Task breakdown + agent assignments
**Speed**: ~35 tok/s
**Context**: 128K tokens

**Prompt template**:
```
You are Coordinator. Analyze request, break into subtasks.
For each subtask output:
- task_id
- agent_type [local|cloud|research]
- complexity [low|medium|high]
- estimated_tokens
```

### 2. Router Agent  
**Rol**: Clasificación rápida de tareas
**Decisiones**:
- `local` → Qwen 32B (code, parsing, simple planning)
- `cloud` → Pony/Claude (complex reasoning, architecture)
- `research` → APIs + web search
- `vision` → FLUX/SVD local

**Ejemplos de routing**:
```
"Crea una función Python" → local
"Diseña la arquitectura de un sistema distribuido" → cloud
"Resume estos 5 papers" → cloud (research)
"Genera imagen prompt" → local → local vision (FLUX)
```

### 3. Parser/Formatter
**Rol**: Output formatting consistente
**Tareas**:
- Convertir output a JSON
- Extraer campos específicos
- Normalizar formatos
- Validar estructura

### 4. Code Generator (Simple)
**Rol**: Boilerplate, utilidades, scripts
**No hacer**:
- ❌ Complex algorithms
- ❌ Debug
- ❌ Optimization

**Sí hacer**:
- ✅ Config files
- ✅ API wrappers
- ✅ Data structures
- ✅ CLI tools simples

---

## ☁️ Agentes Cloud (APIs)

### 5. Architecture Agent (Pony-Alpha / Aurora)
**Trigger**: complexity=high en routing
**Tareas**:
- System design
- Algorithm selection
- Trade-off analysis
- Best practices research

### 6. Code Review Agent (Claude Sonnet)
**Trigger**: code from local needs review
**Tareas**:
- Bug detection
- Optimization suggestions
- Security review
- Style enforcement

### 7. Research Synthesis Agent (Claude)
**Trigger**: research=required
**Tareas**:
- Information gathering
- Synthesis
- Comparison analysis
- Recommendation

---

## 🗂️ Estructura de Datos

### Task Object
```json
{
  "task_id": "uuid",
  "origin": "user|agent",
  "content": "string",
  "complexity": "low|medium|high",
  "route": "local|cloud|research|vision",
  "assigned_agent": "coordinator|router|parser|code|claude|pony|aurora",
  "status": "pending|assigned|processing|completed|failed",
  "output": "any",
  "tokens_used": 0,
  "cost": 0.0,
  "latency_ms": 0,
  "dependencies": ["task_id"],
  "created_at": "timestamp",
  "completed_at": "timestamp"
}
```

### Agent Registry
```json
{
  "qwen-32b": {
    "type": "local",
    "endpoint": "ollama://localhost:11434",
    "model": "qwen2.5:32b",
    "vram_gb": 20,
    "speed_tok_s": 35,
    "strengths": ["routing", "parsing", "simple_code", "planning"],
    "cost_per_1k": 0
  },
  "claude-sonnet": {
    "type": "cloud",
    "provider": "anthropic",
    "model": "claude-sonnet-4",
    "strengths": ["reasoning", "code_review", "research"],
    "cost_per_1k": 0.003
  },
  "pony-alpha": {
    "type": "cloud",
    "provider": "openrouter",
    "model": "openrouter/nova-pt-pairwise",
    "strengths": ["reasoning", "agentic_workflows"],
    "cost_per_1k": 0.002
  },
  "aurora-alpha": {
    "type": "cloud",
    "provider": "openrouter",
    "model": "openrouter/aurora-alpha",
    "cost_per_1k": 0
  }
}
```

---

## 📊 Decision Tree (Coordinator Logic)

```
IF request.contains("architecture|design|system"):
    → cloud (Pony/Claude)
    
ELSE IF request.contains("debug|optimize|review code"):
    → cloud (Claude review)
    
ELSE IF request.contains("research|synthesize|compare"):
    → cloud (Claude research)
    
ELSE IF request.contains("generate image|video"):
    → local vision (FLUX/SVD)
    
ELSE IF tokens_estimated > 2000:
    → cloud (context handling)
    
ELSE IF complexity == "complex":
    → cloud
    
ELSE:
    → local (Qwen 32B)
```

---

## 💾 VRAM Allocation (RTX 3090 24GB)

```
┌─────────────────────────────────────┐
│  VRAM Total: 24 GB                  │
├─────────────────────────────────────┤
│  Qwen 2.5 32B:     20 GB (83%)     │
│  (locked, exclusivo)                │
├─────────────────────────────────────┤
│  FLUX.1-schnell:   ~1 GB (4%)      │
│  (on-demand, offloadable)           │
├─────────────────────────────────────┤
│  SVD XT:            ~2 GB (8%)     │
│  (on-demand, offloadable)           │
├─────────────────────────────────────┤
│  Buffer/Sistema:    ~1 GB (5%)     │
└─────────────────────────────────────┘
     TOTAL USADO: 100%
     
Nota: FLUX/SVD se cargan dinámicamente
si Qwen no está generando (context idle > 60s)
```

---

## 🔌 API Integration (Cloud)

### Priority Order
1. **Pony-Alpha** (OpenRouter) - Primary cloud
2. **Aurora Alpha** (OpenRouter) - Free backup for reasoning
3. **Claude Sonnet** (Anthropic) - Premium when needed

### Fallback Chain
```
User Request → Coordinator → [try Pony (fast)] → [timeout? try Aurora (free)] → [fail? try Claude (reliable)]
```

---

## ⚡ Performance Targets

| Métrica | Target | Actual (Qwen) |
|---------|--------|---------------|
| Local routing | < 3s | ✅ ~2.7s |
| Local code gen | < 15s | ✅ ~11s |
| Cloud response | < 10s | ~8s |
| Total orchestration | < 5s | TBD |
| Cost per interaction | <$0.01 | Variable |

---

## 🚀 Deployment

### Startup Script
```bash
#!/bin/bash
# Start Qwen 32B (dedicated)
ollama run qwen2.5:32b &

# Start OpenClaw Gateway  
openclaw gateway start &

# Start Dashboard
python /home/lumen/lumenai-workspace/lumen_dashboard/app.py &

echo "LumenAGI SWARM Ready"
echo "Qwen 32B: ollama://localhost:11434"
echo "Gateway: ws://localhost:18789"
```

---

## ✅ Checklist de Aprobación

- [x] Qwen 32B dedicado 20GB VRAM
- [x] Cloud APIs para reasoning complejo
- [x] Router automático sin intervención
- [x] Parser local para formatting
- [x] Coordinator como punto único
- [x] Cost optimization (80/20 rule)
- [ ] Implementación inicial
- [ ] Testing con requests reales
- [ ] Tuning basado en métricas

---

**Status**: 🟢 **APROBADO** por Humberto
**Versión**: v1.0
**Fecha**: 2026-02-11
