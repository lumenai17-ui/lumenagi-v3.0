# 🏗️ LumenAGI SWARM Architecture v2.0
## VRAM Exclusiva: Qwen 32B (Cabeza) + Todo lo demás por API

---

## 📋 Resumen Ejecutivo

| Componente | Ubicación | VRAM/Costo | Rol |
|------------|-----------|------------|-----|
| **🧠 COORDINATOR (Cabeza)** | **Qwen 32B Local** | **20GB VRAM (EXCLUSIVO)** | Orquestador único |
| Router Agent | Qwen 32B (comparte) | $0 | Clasificación de tareas |
| Parser/Formatter | Qwen 32B (comparte) | $0 | JSON, estructuras |
| Simple Coder | Qwen 32B (comparte) | $0 | Boilerplate, utilidades |
| Planner | Qwen 32B (comparte) | $0 | Task decomposition simple |
| **Complex Reasoning** | Aurora Alpha | API $0 | Razonamiento profundo |
| **Code Review** | Claude Sonnet | API $ | Debug, optimización |
| **Research** | Claude Sonnet | API $ | Análisis complejo |
| **Vision (img/vid)** | APIs externas | API $ | Stability, Replicate, etc. |

**⚠️ NOTA**: Kimi K2.5 fue reemplazado por Qwen 32B como modelo local.
**⚠️ NOTA**: FLUX/SVD salen de VRAM → usan APIs de terceros.

---

## 🎯 Principios de Diseño (Simplificado)

1. **UN modelo en VRAM**: Qwen 32B es la cabeza, punto único de entrada
2. **Todo lo demás es API**: Imágenes, video, reasoning complejo
3. **Auto-routing**: Coordinator decide local vs cloud vs vision
4. **Sin colisiones**: 20GB VRAM exclusivos, nada más compite

---

## 🔄 Flujo de Trabajo (User Request)

```
┌─────────────────────────────────────────────────────────────┐
│  USUARIO: "Crea un sistema de agentes para X"                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  🧠 COORDINATOR (Qwen 32B) — LA CABEZA                      │
│  • Analiza el request                                         │
│  • Decide: local / cloud / vision                            │
│  • Descompone en sub-tareas                                   │
│  • Orquesta ejecución                                         │
└────────────────────┬──────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬─────────────┐
        ▼            ▼            ▼             ▼
   ┌────────┐   ┌────────┐   ┌──────────┐  ┌──────────┐
   │Local   │   │Cloud   │   │Vision    │  │Research  │
   │Qwen    │   │Aurora  │   │APIs      │  │Claude    │
   │Parsing │   │Claude  │   │(img/vid) │  │Web       │
   └────┬───┘   └────┬───┘   └────┬─────┘  └────┬─────┘
        │            │            │             │
        └────────────┴────────────┴─────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PARSER (Qwen 32B) — Estructura respuesta final             │
└────────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
                    USUARIO
```

---

## 🧠 ¿Quién es la Cabeza?

### **Qwen 2.5 32B = COORDINATOR ÚNICO**

**Rol**: Único modelo en VRAM, orquesta todo
**Ubicación**: Local (Ollama)
**VRAM**: 20GB dedicados, exclusivos
**Contexto**: 128K tokens
**Velocidad**: ~35 tokens/s

**Kimi K2.5 fue reemplazado** - ahora todo pasa por Qwen 32B.

### Responsabilidades del Coordinator:
1. Recibir user request
2. Analizar complejidad
3. Decidir ruta (local/cloud/vision/research)
4. Descomponer en sub-tareas
5. Asignar a agents
6. Recolectar outputs
7. Parsear respuesta final

---

## 🤖 Agentes Locales (Qwen 32B)

### 1. Coordinator (Cabeza)
**Input**: User request  
**Output**: Decision + Task breakdown  
**VRAM**: 20GB exclusivos

**Prompt template**:
```
You are Coordinator. Analyze request and decide:

ROUTE: [local|cloud_reasoning|cloud_code|vision_api|research]
COMPLEXITY: [low|medium|high]

Subtasks:
- task_id
- type: [local_parse|local_code|cloud_claude|cloud_aurora|api_vision]
- description
- estimated_tokens
```

### 2. Router Agent
**Rol**: Clasificación rápida

| Request | Decisión |
|---------|----------|
| "Crea función Python" | local_code |
| "Diseña arquitectura" | cloud_claude |
| "Genera imagen" | api_vision |
| "Resume papers" | cloud_claude + web_search |
| "Razona paso a paso" | cloud_aurora (free) |

### 3. Parser Agent
**Rol**: Formatting universal
- JSON structuring
- Field extraction
- Response templating
- Error normalization

### 4. Code Generator
**Rol**: Simple boilerplate
- Config files
- API wrappers
- Data structures
- Test templates

**LIMITACIÓN**: No debug, no optimize, no complex algorithms

---

## ☁️ Agentes Cloud (APIs)

### 5. Complex Reasoning → Aurora Alpha
**Proveedor**: OpenRouter  
**Costo**: $0 (free tier)  
**Uso**: Paso a paso, chain-of-thought  
**Cuándo**: Coordinator marca `complexity=high` + reasoning

### 6. Code Review → Claude Sonnet
**Proveedor**: Anthropic  
**Costo**: ~$0.003/1K tokens  
**Uso**: Debug, optimize, review  
**Cuándo**: Post-code generation local

### 7. Research → Claude Sonnet
**Proveedor**: Anthropic  
**Costo**: ~$0.003/1K tokens  
**Uso**: Synthesis, best practices, current info  
**Cuándo**: `research=required`

### 8. Vision → APIs Externas
**Imágenes**: Stability AI, Replicate, DALL-E  
**Video**: Runway, Pika, HeyGen  
**Costo**: Variable (~$0.01-0.10/img)  
**Cuándo**: `vision=required`

**⚠️ FLUX/SVD YA NO ESTÁN EN VRAM**

---

## 🔌 APIs Activas

```json
{
  "cloud_agents": {
    "aurora-alpha": {
      "provider": "openrouter",
      "model": "openrouter/aurora-alpha",
      "cost": "$0",
      "use": "reasoning, step-by-step",
      "fallback": "claude"
    },
    "claude-sonnet": {
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514",
      "cost": "$3/1M tokens",
      "use": "code_review, research, complex_architecture"
    }
  },
  "vision_apis": {
    "stability": {
      "use": "image_generation",
      "cost": "$0.01-0.05/img"
    },
    "replicate": {
      "use": "video_generation",
      "cost": "$0.10-0.50/video"
    }
  }
}
```

---

## 💾 VRAM Exclusiva (RTX 3090 24GB)

```
┌─────────────────────────────────────────────┐
│  VRAM Total: 24 GB                        │
├─────────────────────────────────────────────┤
│  🔒 Qwen 2.5 32B:     20 GB (83%)        │
│     COORDINATOR — EXCLUSIVO, SIEMPRE ON  │
├─────────────────────────────────────────────┤
│  🔄 Buffer dinámico:   4 GB (17%)        │
│     Para operaciones temporales             │
└─────────────────────────────────────────────┘

❌ FLUX — fuera de VRAM (usa API)
❌ SVD — fuera de VRAM (usa API) 
❌ Kimi K2.5 — reemplazado por Qwen 32B

✅ SOLO Qwen 32B reside en VRAM
```

---

## 📊 Decision Tree (Coordinator)

```python
IF "generate image OR video" in request:
    → api_vision (Stability, Replicate)
    
ELIF "research current info" in request:
    → cloud_claude + web_search
    
ELIF "architecture design OR system design" in request:
    → cloud_claude (complex)
    
ELIF "debug OR optimize code" in request:
    → cloud_claude (code_review)
    
ELIF "reasoning step-by-step" in request:
    → cloud_aurora (free)
  
ELIF "simple code OR parse OR format" in request:
    → local_qwen
    
ELSE:
    → local_qwen (default)
```

---

## ⚡ Performance Esperado

| Operación | Modelo | Tiempo Esperado |
|-----------|--------|-----------------|
| Routing | Qwen 32B | ~3s |
| Parsing | Qwen 32B | ~3s |
| Code simple | Qwen 32B | ~12s |
| Reasoning | Aurora | ~10s |
| Code review | Claude | ~8s |
| Research | Claude | ~15s |

**Costo mensual estimado** (1000 requests):
- 800 local: **$0**
- 150 Aurora: **$0**
- 50 Claude: **~$5-10**
- **Total: ~$5-10/mes**

---

## 🚀 Startup (Qwen 32B Exclusivo)

```bash
#!/bin/bash
echo "🚀 Starting LumenAGI SWARM v2.0"

# 1. Verificar VRAM libre
nvidia-smi --query-gpu=memory.free --format=csv,noheader

# 2. Cargar COORDINATOR (único en VRAM)
echo "Loading Qwen 32B (Coordinator)..."
ollama run qwen2.5:32b &

# 3. Esperar carga completa
sleep 120
echo "✅ Qwen 32B loaded — 20GB VRAM locked"

# 4. Start Gateway
openclaw gateway start &

echo "🎯 Ready: Coordinator (Qwen 32B) at ollama://localhost:11434"
echo "☁️  Cloud ready: Aurora ($0), Claude ($$$)"
echo "📸 Vision ready: Stability API, Replicate API"
```

---

## ✅ Checklist v2.0

- [x] **Qwen 32B = Cabeza exclusiva (20GB VRAM)**
- [x] **Pony Alpha eliminado** → reemplazado por Aurora Alpha
- [x] **Kimi K2.5 reemplazado** → ahora Qwen 32B es el único local
- [x] **FLUX/SVD fuera de VRAM** → APIs externas
- [x] **Aurora Alpha** → reasoning gratuito
- [x] **Claude Sonnet** → code review + research
- [x] **Vision APIs** → Stability, Replicate (no local)
- [x] VRAM exclusiva sin competencia
- [ ] Implementación inicial
- [ ] Testing end-to-end

---

**Status**: 🟡 **PENDIENTE DE APROBACIÓN** v2.0
**Cambios**: Pony out, Kimi out, FLUX/SVD out, VRAM exclusiva para Qwen 32B
**Fecha**: 2026-02-11
