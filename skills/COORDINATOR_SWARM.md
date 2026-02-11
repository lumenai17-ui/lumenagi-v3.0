# Skill: Coordinator SWARM

## What It Does
Orquestador multi-agente que divide tareas complejas y las asigna a agentes especializados según la arquitectura v3.0.

## Architecture
```
Usuario Request → Coordinator (Kimi) → Analysis
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   Qwen (Local)    GPT-4o (API)    Vision API
   Code/Parse      Research        Img/Video
```

## Code
```python
class SWARMCoordinator:
    AGENT_MODELS = {
        AgentType.CODE_LOCAL: "ollama/qwen2.5:32b",
        AgentType.RESEARCH: "openai/gpt-4o",
        AgentType.VISION: "vision_api",
    }
    
    def analyze_request(self, user_request: str) -> Dict:
        # Keywords routing
        if "investiga" in request: needs_research = True
        if "código" in request: needs_code = True
        return {"needs_research": needs_research, "needs_code": needs_code}
    
    def create_plan(self, analysis: Dict) -> List[SubTask]:
        # Divide en tareas con dependencias
        tasks = []
        if analysis["needs_research"]:
            tasks.append(SubTask(agent=AgentType.RESEARCH, ...))
        if analysis["needs_code"]:
            tasks.append(SubTask(agent=AgentType.CODE_LOCAL, ...))
        return tasks
```

## Decision Tree
| Keywords | Agente | Modelo | Costo |
|----------|--------|--------|-------|
| "investiga", "research" | research | GPT-4o | $ |
| "código", "genera", "python" | code_local | Qwen 32B | $0 |
| "imagen", "video" | vision | API | $ |
| default | code_local | Qwen 32B | $0 |

## Installation
```python
# Copy coordinator_swarm.py to workspace
from coordinator_swarm import SWARMCoordinator

coordinator = SWARMCoordinator()
result = coordinator.run("Investiga FastAPI y genera boilerplate")
# Returns: {"plan": [...], "results": {...}, "final_response": "..."}
```

## Lessons Learned
- Decision tree simple con keywords funciona 80% de casos
- Más complejidad → usar LLM para routing
- Cada subtarea debe tener output_format específico
- Dependencies importantes para orden de ejecución

## Reuse
Adapt for any multi-step workflow:
- Research → Code → Review pipeline
- Data ingestion → Transform → Analysis
- Image gen → Variation → Selection
