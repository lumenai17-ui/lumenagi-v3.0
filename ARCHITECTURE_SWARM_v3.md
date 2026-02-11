# 🏗️ LumenAGI SWARM Architecture v3.0
## Kimi Cerebro (Cloud) + Qwen Agente (Local 20GB VRAM)

---

## 📋 Resumen Ejecutivo

| Rol | Modelo | Ubicación | VRAM/Costo | Función |
|-----|--------|-----------|------------|---------|
| **🧠 CEREBRO** | **Kimi K2.5** | **Ollama Cloud** | **$0 con Ollama Pro** | Coordinator, decisión, orquestación |
| **⚡ AGENTE** | **Qwen 2.5 32B** | **Local (Ollama)** | **20GB VRAM exclusiva** | Ejecución, parsing, code simple |
| **🔧 Code Review** | Claude Sonnet | Anthropic API | ~$3/1M tokens | Debug, optimize, review |
| **📚 Research** | Claude Sonnet | Anthropic API | ~$3/1M tokens | Synthesis, best practices |
| **🎨 Vision** | Stability/Replicate | APIs externas | variable | Img/video generation |

**⚠️ NO usamos OpenRouter** (Pony/Aurora fallan)  
**✅ Kimi cloud + Qwen local = sin conflicto VRAM**

---

## 🎯 Principios de Diseño

1. **Kimi = Cerebro** (cloud): Decide, planea, orquesta
2. **Qwen = Músculo** (local): Ejecuta, genera, parsea
3. **Sin conflicto VRAM**: Kimi está en cloud, Qwen en local
4. **Sin OpenRouter**: Claude directo cuando necesitamos más

---

## 🔄 Flujo de Trabajo

```
┌─────────────────────────────────────────────────────────────┐
│  USUARIO: "Crea un sistema de agentes para X"                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  🧠 CEREBRO (Kimi K2.5 — Ollama Cloud)                      │
│  • Analiza requerimiento                                      │
│  • Decide plan de acción                                       │
│  • Descompone en micro-tareas                                  │
│  • Asigna cada tarea al agente apropiado                       │
└────────────────────┬──────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬─────────────┐
        ▼            ▼            ▼             ▼
   ┌────────┐   ┌────────┐   ┌──────────┐  ┌──────────┐
   │Qwen    │   │Claude  │   │Vision    │  │Research  │
   │32B     │   │Sonnet  │   │APIs      │  │Claude    │
   │Local   │   │API     │   │(img/vid) │  |Web       │
   └────┬───┘   └────┬───┘   └────┬─────┘  └────┬─────┘
        │            │            │             │
        └────────────┴────────────┴─────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  🧠 CEREBRO (Kimi) — Compila respuesta final                │
└────────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
                    USUARIO
```

---

## 🧠 CEREBRO: Kimi K2.5 (Ollama Cloud)

**Ubicación**: Cloud (Ollama Pro)  
**Costo**: $0 con tu suscripción Pro  
**VRAM local**: 0GB (está en cloud)  
**Contexto**: Grande (256K+)  
**Velocidad**: Depende de red, pero calidad superior

### Responsabilidades del Cerebro:
1. **Entender** el request del usuario
2. **Planear** secuencia de acciones
3. **Decidir** qué agente ejecuta cada tarea
4. **Coordinar** dependencias entre tareas
5. **Compilar** outputs en respuesta final coherente

### Prompt del Cerebro:
```
You are the BRAIN of a multi-agent system.

Available agents:
- QWEN_LOCAL: Fast, cheap, good for simple tasks, code, parsing
- CLAUDE_API: High quality, expensive, for complex reasoning/research
- VISION_API: For image/video generation

User request: {input}

Output JSON:
{
  "plan": "high-level strategy",
  "tasks": [
    {
      "task_id": 1,
      "agent": "QWEN_LOCAL|CLAUDE_API|VISION_API",
      "instruction": "detailed instruction for this agent",
      "depends_on": []
    }
  ]
}
```

---

## ⚡ AGENTE: Qwen 2.5 32B (Local)

**Ubicación**: Local (Ollama)  
**VRAM**: 20GB exclusivos  
**Costo**: $0  
**Contexto**: 128K  
**Velocidad**: ~35 tokens/s

### Tareas del Agente:
- ✅ Code generation simple (boilerplate, utilidades)
- ✅ JSON parsing y formatting
- ✅ Data extraction
- ✅ Response templating  
- ✅ Transformaciones de texto
- ✅ Validaciones simples

### NO hace:
- ❌ Decisiones de arquitectura
- ❌ Debugging profundo
- ❌ Research complejo
- ❌ Chain-of-thought reasoning

**El Agente ejecuta, el Cerebro decide.**

---

## 💾 VRAM Asignada (Limpia)

```
RTX 3090 24GB:
├─ 🔒 Qwen 2.5 32B:     20 GB (AGENTE — EXCLUSIVO)
├─ 🔄 Buffer sistema:    ~2 GB 
└─ 📦 Cache/overflow:     ~2 GB (dinámico)

Total usado: ~20-22GB (deja margen)

NOTA: Kimi K2.5 NO usa VRAM local (cloud)
```

---

## 🔌 APIs de Soporte (Cuando Qwen no alcanza)

### Claude Sonnet (Anthropic)
```
Para: Code review, debugging, research, complex reasoning
Trigger: Cerebro decide "esto necesita mejor calidad"
Costo: ~$3 por millón de tokens
```

### Vision APIs (Stability, Replicate, etc.)
```
Para: Images, videos
Trigger: User pide visual content
Costo: variable ($0.01-0.50)
```

---

## 📊 Decision Tree (Cerebro Kimi)

```
Cerebro analiza request:

IF "user pide imagen o video":
    → Agente = VISION_API
    → Qwen no involucrado
    
ELIF "necesita investigar info actual":
    → Agente = CLAUDE_API + web_search
    → Qwen no involucrado
    
ELIF "es código simple, boilerplate, utilidad":
    → Agente = QWEN_LOCAL (rápido, gratis)
    → INSTRUCCIÓN: genera código con type hints
    
ELIF "es parseo, JSON, estructuración":
    → Agente = QWEN_LOCAL (rápido, obediente)
    → INSTRUCCIÓN: output solo JSON válido
    
ELIF "code review, debug, optimización":
    → Agente = CLAUDE_API (mejor calidad)
    → Qwen puede haber generado el código original
    
ELIF "razonamiento complejo, arquitectura":
    → Agente = CLAUDE_API
    → Cerebro delega el thinking pesado
    
ELSE (default):
    → Agente = QWEN_LOCAL
```

---

## 🔄 Ejemplo de Flujo Real

**Usuario**: "Crea un scraper para extraer precios de Amazon y guardarlos en CSV"

```
1. 🧠 CEREBRO (Kimi) recibe request
   → Analiza: necesita scraper, requests, parsing
   → Plan: 
     a) Generar código scraper (simple) → QWEN_LOCAL
     b) Revisar código por errores → CLAUDE_API (opcional)
  
2. ⚡ AGENTE (Qwen 32B) ejecuta (a)
   → Genera: scraper.py con requests, BeautifulSoup, pandas
   → Tiempo: ~10s, Costo: $0
   
3. 🧠 CEREBRO compila
   → Devuelve: código + instrucciones de uso al usuario
```

**Usuario**: "Diseña la arquitectura de un sistema de agentes distribuidos con fault tolerance"

```
1. 🧠 CEREBRO (Kimi) recibe request
   → Analiza: complejo, arquitectura, trade-offs
   → Plan:
     a) Diseñar arquitectura → CLAUDE_API (razonamiento profundo)
     b) Generar boilerplate configs → QWEN_LOCAL
     
2. 🔧 CLAUDE genera diseño arquitectónico
   → Diagrama, componentes, patrones
   
3. ⚡ QWEN genera configs basado en el diseño
   → docker-compose.yml, k8s manifests
   → Tiempo: ~8s, Costo: $0
   
4. 🧠 CEREBRO integra
   → Devuelve: diseño completo + código de configuración
```

---

## ⚡ Performance

| Rol | Modelo | Típico | Costo |
|-----|--------|--------|-------|
| Cerebro | Kimi K2.5 | ~5-10s | $0 (Pro) |
| Agente | Qwen 32B | ~3-12s | $0 (20GB VRAM) |
| Review | Claude | ~8-15s | ~$0.005-0.02 |
| Research | Claude | ~15-30s | ~$0.01-0.05 |

---

## 🚀 Startup

```bash
#!/bin/bash
echo "🚀 Starting LumenAGI SWARM v3.0"
echo "🧠 Cerebro: Kimi K2.5 (Ollama Cloud)"
echo "⚡ Agente: Qwen 32B (Local VRAM)"

# Verificar VRAM
nvidia-smi

# Cargar Agente Qwen (único en VRAM local)
echo "Cargando Qwen 32B..."
ollama run qwen2.5:32b &

sleep 120

echo "✅ Ready:"
echo "  🧠 Kimi (cloud): ollama://kimi-k2.5 (via Ollama Pro)"
echo "  ⚡ Qwen (local): ollama://localhost:11434"
echo "  🔧 Claude (API): anthropic://claude-sonnet-4"
```

---

## ✅ Checklist v3.0

- [x] **Kimi K2.5 = CEREBRO** (cloud, no VRAM local)
- [x] **Qwen 32B = AGENTE** (local, 20GB VRAM exclusiva)
- [x] **Sin conflicto**: Kimi cloud + Qwen local funcionan juntos
- [x] **Tareas divididas**: Kimi piensa, Qwen ejecuta
- [x] **NO OpenRouter**: Claude directo como fallback
- [x] **Vision**: APIs externas (no local)
- [ ] Implementar primera versión
- [ ] Test de integración Kimi ↔ Qwen

---

**Status**: 🟡 **PENDIENTE APROBACIÓN v3.0**
**Corección**: Kimi = Cerebro (cloud), Qwen = Agente (local 20GB)
**Fecha**: 2026-02-11
