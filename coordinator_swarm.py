#!/usr/bin/env python3
"""
LumenAGI SWARM Coordinator v1.0
Arquitectura: Kimi Cerebro (Cloud) + Qwen Agente (Local 20GB VRAM)

Este Coordinator recibe tareas del usuario, las descompone,
y las asigna a los agentes apropiados según la arquitectura v3.0.
"""

import json
import subprocess
from typing import Dict, List, Any, Literal
from dataclasses import dataclass
from enum import Enum

class AgentType(Enum):
    """Tipos de agentes disponibles en el SWARM"""
    COORDINATOR = "coordinator"      # Kimi K2.5 - decisiones, orquestación
    CODE_LOCAL = "code_local"        # Qwen 32B - código simple, parsing
    RESEARCH = "research"            # Claude Sonnet - investigación profunda
    CODE_REVIEW = "code_review"      # Claude Sonnet - revisión/debug
    VISION = "vision"                # APIs - imágenes/video

@dataclass
class SubTask:
    """Una subtarea del plan"""
    id: str
    agent_type: AgentType
    description: str
    input_data: Dict[str, Any]
    output_format: str
    max_tokens: int = 1000
    depends_on: List[str] = None
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []

class SWARMCoordinator:
    """
    El Coordinator principal (Kimi K2.5 como cerebro)
    
    Decision Tree:
    - "investiga/research" -> Claude
    - "código simple/generate" -> Qwen 32B  
    - "revisar/debug" -> Claude
    - "imagen/video" -> Vision APIs
    """
    
    AGENT_MODELS = {
        AgentType.COORDINATOR: "ollama/kimi-k2.5:cloud",
        AgentType.CODE_LOCAL: "ollama/qwen2.5:32b",
        AgentType.RESEARCH: "openai/gpt-4o",  # OpenAI en lugar de Claude
        AgentType.CODE_REVIEW: "openai/gpt-4o",  # OpenAI en lugar de Claude
        AgentType.VISION: "vision_api",
    }
    
    def __init__(self):
        self.session_history = []
        
    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """
        Fase 1: Análisis por Kimi (este Coordinator mismo)
        Decide qué agentes necesita la tarea
        """
        # Keywords para routing
        if any(kw in user_request.lower() for kw in 
                ["research", "investiga", "busca", "encuentra", "best practices"]):
            needs_research = True
        else:
            needs_research = False
            
        if any(kw in user_request.lower() for kw in 
                ["code", "genera código", "función", "python", "boilerplate"]):
            needs_code = True
        else:
            needs_code = False
            
        if any(kw in user_request.lower() for kw in 
                ["revisa", "debug", "optimiza", "corregir", "review"]):
            needs_review = True
        else:
            needs_review = False

        return {
            "needs_research": needs_research,
            "needs_code": needs_code,
            "needs_review": needs_review,
            "original_request": user_request
        }
    
    def create_plan(self, analysis: Dict[str, Any]) -> List[SubTask]:
        """
        Fase 2: Creación del plan de ejecución
        """
        tasks = []
        task_id = 0
        
        # Si necesita investigación -> primero Research
        if analysis["needs_research"]:
            task_id += 1
            tasks.append(SubTask(
                id=f"T{task_id}",
                agent_type=AgentType.RESEARCH,
                description=f"Investigar: {analysis['original_request']}",
                input_data={"query": analysis["original_request"]},
                output_format="Resumen estructurado con fuentes y best practices",
                max_tokens=2000
            ))
        
        # Si necesita código -> luego Code (puede depender de research)
        if analysis["needs_code"]:
            task_id += 1
            task_deps = [tasks[-1].id] if tasks else []
            tasks.append(SubTask(
                id=f"T{task_id}",
                agent_type=AgentType.CODE_LOCAL,
                description="Generar código basado en requerimientos",
                input_data={
                    "request": analysis["original_request"],
                    "context": "Usar best practices encontradas"
                },
                output_format="Código Python con type hints y docstrings",
                max_tokens=1500,
                depends_on=task_deps
            ))
        
        # Si necesita revisión -> al final Code Review
        if analysis["needs_review"]:
            task_id += 1
            task_deps = [tasks[-1].id] if tasks else []
            tasks.append(SubTask(
                id=f"T{task_id}",
                agent_type=AgentType.CODE_REVIEW,
                description="Revisar y optimizar código generado",
                input_data={
                    "code": "{{output_T" + str(task_id-1) + "}}",
                    "criteria": "Type hints, docstrings, error handling, seguridad"
                },
                output_format="Código revisado con comentarios de mejoras",
                max_tokens=2000,
                depends_on=task_deps
            ))
        
        return tasks
    
    def execute_task(self, task: SubTask) -> str:
        """
        Fase 3: Ejecutar subtarea en el agente asignado
        """
        model = self.AGENT_MODELS[task.agent_type]
        
        # Construir prompt según el agente
        prompt = self._build_agent_prompt(task)
        
        # Ejecutar según el modelo
        if model == "vision_api":
            return self._call_vision_api(task)
        elif "ollama/" in model:
            return self._call_ollama(model, prompt, task.max_tokens)
        elif "anthropic/" in model:
            return self._call_claude(prompt, task.max_tokens)
        else:
            return f"Error: Modelo no soportado: {model}"
    
    def _build_agent_prompt(self, task: SubTask) -> str:
        """Construir prompt específico para cada tipo de agente"""
        prompts = {
            AgentType.CODE_LOCAL: f"""
Actúa como un generador de código Python eficiente.

TAREA: {task.description}

REQUISITOS:
- Type hints obligatorios
- Docstrings completas
- Funciones pequeñas y claras
- Manejo básico de errores con try/except
- Solo devuelve el código, sin explicaciones

FORMATO SALIDA:
{task.output_format}
""",
            AgentType.RESEARCH: f"""
Eres un investigador experto en arquitectura de software y mejores prácticas.

CONSULTA: {task.description}

Realiza una búsqueda exhaustiva y proporciona:
1. Resumen de findings principales
2. Fuentes relevantes (papers, docs, repos)
3. Best practices específicas aplicables
4. Recomendaciones de implementación

FORMATO: JSON estructurado con campos: summary, sources, best_practices, recommendations
""",
            AgentType.CODE_REVIEW: f"""
Eres un reviewer senior de código Python.

CÓDIGO A REVISAR: {task.description}

CRITERIOS DE REVISIÓN:
1. Type hints presentes y correctos
2. Docstrings descriptivas
3. Manejo de errores robusto
4. Eficiencia y optimización
5. Seguridad básica

SALIDA:
- Código revisado y mejorado
- Lista de cambios realizados
- Ejemplo de uso si aplica
"""
        }
        return prompts.get(task.agent_type, task.description)
    
    def _call_ollama(self, model: str, prompt: str, max_tokens: int) -> str:
        """Llamar a modelo local (Qwen 32B o Kimi)"""
        model_name = model.split("/")[-1]  # Extrae "qwen2.5:32b"
        
        data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7
            }
        }
        
        try:
            import urllib.request
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode())
                return result.get("response", "Error: No response")
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"
    
    def _call_claude(self, prompt: str, max_tokens: int) -> str:
        """Placeholder - requiere integración con Anthropic API"""
        return f"[Claude API call needed] Task: {prompt[:100]}..."
    
    def _call_vision_api(self, task: SubTask) -> str:
        """Placeholder para APIs de visión"""
        return "[Vision API call needed]"
    
    def run(self, user_request: str) -> Dict[str, Any]:
        """
        Punto de entrada principal
        """
        print(f"🧠 Coordinator recibió: {user_request[:80]}...")
        
        # Fase 1: Análisis
        analysis = self.analyze_request(user_request)
        print(f"📊 Análisis: research={analysis['needs_research']}, code={analysis['needs_code']}, review={analysis['needs_review']}")
        
        # Fase 2: Plan
        plan = self.create_plan(analysis)
        print(f"📋 Plan creado: {len(plan)} tareas")
        for task in plan:
            print(f"   - T{task.id}: {task.agent_type.value} ({task.description[:50]}...)")
        
        # Fase 3: Ejecución
        results = {}
        for task in plan:
            print(f"\n⚡ Ejecutando T{task.id} con {task.agent_type.value}...")
            result = self.execute_task(task)
            results[task.id] = result
            print(f"   ✅ T{task.id} completado ({len(result)} chars)")
        
        # Fase 4: Integración
        final_response = self._integrate_results(results, analysis)
        
        return {
            "request": user_request,
            "analysis": analysis,
            "plan": [{"id": t.id, "agent": t.agent_type.value, "desc": t.description} for t in plan],
            "results": results,
            "final_response": final_response
        }
    
    def _integrate_results(self, results: Dict[str, str], analysis: Dict[str, Any]) -> str:
        """Integrar resultados de todos los agentes"""
        parts = ["🎯 Resultado del Sistema Multi-Agente SWARM:\n"]
        
        for task_id, result in results.items():
            parts.append(f"\n--- Agent {task_id} ---\n{result[:500]}...")
        
        return "\n".join(parts)


# Demo/Testing
if __name__ == "__main__":
    coordinator = SWARMCoordinator()
    
    # Test 1: Solo código
    print("="*60)
    print("TEST 1: Generar función simple")
    print("="*60)
    result = coordinator.run("Crea una función Python que calcule el factorial")
    print(f"\n{result['final_response']}")
    
    # Test 2: Investigación + código
    print("\n" + "="*60)
    print("TEST 2: Research + Code")
    print("="*60)
    result = coordinator.run("Investiga best practices de FastAPI y genera estructura de proyecto")
    print(f"\n{result['final_response']}")
