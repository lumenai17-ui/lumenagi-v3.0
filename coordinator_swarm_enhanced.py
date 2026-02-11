#!/usr/bin/env python3
"""
LumenAGI SWARM Coordinator v1.1 — Enhanced with Tool Plugin
Arquitectura: Kimi Cerebro (Cloud) + Qwen Agente (Local) + Tool Plugin

Integración gradual: mantiene el core v1.0, agrega tool selection como plugin
"""

import json
import subprocess
import sys
from typing import Dict, List, Any, Literal
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, '/home/lumen/.openclaw/workspace')
from coordinator_tool_plugin import CoordinatorToolPlugin, enhance_swarm_coordinator


class AgentType(Enum):
    """Tipos de agentes disponibles en el SWARM"""
    COORDINATOR = "coordinator"
    CODE_LOCAL = "code_local"
    RESEARCH = "research"
    CODE_REVIEW = "code_review"
    VISION = "vision"


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
    required_tools: List[str] = None
    tool_instructions: str = ""
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []
        if self.required_tools is None:
            self.required_tools = []


class SWARMCoordinator:
    """
    El Coordinator principal v1.1 con Tool Plugin integrado
    Compatible hacia atrás con v1.0
    """
    
    AGENT_MODELS = {
        AgentType.COORDINATOR: "ollama/kimi-k2.5:cloud",
        AgentType.CODE_LOCAL: "ollama/qwen2.5:32b",
        AgentType.RESEARCH: "openai/gpt-4o",
        AgentType.CODE_REVIEW: "openai/gpt-4o",
        AgentType.VISION: "vision_api",
    }
    
    def __init__(self, tool_plugin_enabled: bool = True):
        self.session_history = []
        self.tool_plugin = CoordinatorToolPlugin(self) if tool_plugin_enabled else None
        self.use_enhanced = tool_plugin_enabled
        
    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """
        Fase 1: Análisis (ahora con plugin enhancement)
        """
        # Análisis original del coordinator
        original = self._original_analysis(user_request)
        
        # Si plugin está activo, enriquecer
        if self.use_enhanced and self.tool_plugin:
            enhanced = self.tool_plugin.enhance_task_analysis(user_request, original)
            enhanced['execution_plan'] = self.tool_plugin.suggest_execution_plan(user_request, enhanced)
            enhanced['tool_instructions'] = self.tool_plugin.get_tool_instructions(
                enhanced['tool_selection']['recommended_tools']
            )
            return enhanced
        
        return original
    
    def _original_analysis(self, user_request: str) -> Dict:
        """Análisis original del coordinator (sin plugin)"""
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
            "recommended_agent": "research" if needs_research else ("code_local" if needs_code else "main"),
            "original_request": user_request
        }
    
    def create_plan(self, analysis: Dict[str, Any]) -> List[SubTask]:
        """
        Fase 2: Creación del plan de ejecución (con tools si está disponible)
        """
        tasks = []
        task_id = 0
        
        # Extraer información de tools si existe
        tool_selection = analysis.get('tool_selection', {})
        recommended_tools = tool_selection.get('recommended_tools', [])
        tool_instructions = analysis.get('tool_instructions', '')
        
        # Agente enhanced (puede venir del plugin)
        agent_rec = analysis.get('enhanced_agent_recommendation', {})
        chosen_agent = agent_rec.get('agent', 'main')
        
        # Si necesita investigación -> primero Research
        if analysis.get("needs_research"):
            task_id += 1
            tasks.append(SubTask(
                id=f"T{task_id}",
                agent_type=AgentType.RESEARCH,
                description=f"Investigar: {analysis.get('original_request', '')}",
                input_data={"query": analysis.get('original_request', '')},
                output_format="Resumen estructurado con fuentes",
                max_tokens=2000,
                required_tools=['web_search'] if 'web_search' in recommended_tools else [],
                tool_instructions=tool_instructions if 'web_search' in recommended_tools else ""
            ))
        
        # Tarea principal con tools
        task_id += 1
        task_deps = [tasks[-1].id] if tasks else []
        
        # Mapear chosen_agent a AgentType
        agent_type_map = {
            'research': AgentType.RESEARCH,
            'code_local': AgentType.CODE_LOCAL,
            'build-qwen32': AgentType.CODE_LOCAL,
            'create-qwen32': AgentType.CODE_LOCAL,
            'main': AgentType.COORDINATOR,
        }
        agent_type = agent_type_map.get(chosen_agent, AgentType.COORDINATOR)
        
        tasks.append(SubTask(
            id=f"T{task_id}",
            agent_type=agent_type,
            description="Ejecutar tarea con herramientas disponibles",
            input_data={
                "request": analysis.get('original_request', ''),
                "tool_instructions": tool_instructions,
                "available_tools": recommended_tools
            },
            output_format="Resultado de la ejecución con herramientas",
            max_tokens=2000,
            depends_on=task_deps,
            required_tools=recommended_tools,
            tool_instructions=tool_instructions
        ))
        
        # Si necesita revisión
        if analysis.get("needs_review"):
            task_id += 1
            task_deps = [tasks[-1].id]
            tasks.append(SubTask(
                id=f"T{task_id}",
                agent_type=AgentType.CODE_REVIEW,
                description="Revisar resultado",
                input_data={"code": "{{output_previo}}"},
                output_format="Código revisado",
                max_tokens=1500,
                depends_on=task_deps
            ))
        
        return tasks
    
    def execute_task(self, task: SubTask) -> str:
        """
        Fase 3: Ejecutar subtarea con contexto de tools
        """
        model = self.AGENT_MODELS[task.agent_type]
        
        # Construir prompt enriquecido con tools
        prompt = self._build_enriched_prompt(task)
        
        # Ejecutar según el modelo
        if model == "vision_api":
            return self._call_vision_api(task)
        elif "ollama/" in model:
            return self._call_ollama(model, prompt, task.max_tokens)
        elif "anthropic/" in model or "openai/" in model:
            return f"[{model}] {task.description[:50]}... (simulado)"
        else:
            return f"Error: Modelo no soportado: {model}"
    
    def _build_enriched_prompt(self, task: SubTask) -> str:
        """Construir prompt con tool instructions"""
        
        base_prompt = f"""Eres un agente del sistema SWARM LumenAGI.

TAREA: {task.description}
"""
        
        # Agregar instrucciones de tools si existen
        if task.tool_instructions:
            base_prompt += f"\n{task.tool_instructions}\n"
        
        if task.required_tools:
            base_prompt += f"\n⚡ ESTA TAREA REQUIERE: {', '.join(task.required_tools)}\n"
        
        base_prompt += f"\nINPUT DATA: {json.dumps(task.input_data, indent=2)}\n"
        base_prompt += f"\nOUTPUT ESPERADO:\n{task.output_format}\n"
        
        return base_prompt
    
    def _call_ollama(self, model: str, prompt: str, max_tokens: int) -> str:
        """Llamar a Ollama local"""
        model_name = model.split("/")[-1]
        
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
    
    def _call_vision_api(self, task: SubTask) -> str:
        return "[Vision API call needed]"
    
    def run(self, user_request: str) -> Dict[str, Any]:
        """
        Punto de entrada principal — con o sin plugin
        """
        mode = "ENHANCED + TOOLS" if self.use_enhanced else "VANILLA"
        print(f"🧠 Coordinator [{mode}] recibió: {user_request[:80]}...")
        
        # Fase 1: Análisis
        analysis = self.analyze_request(user_request)
        print(f"📊 Análisis: research={analysis.get('needs_research')}, code={analysis.get('needs_code')}, review={analysis.get('needs_review')}")
        
        # Mostrar info del plugin si existe
        if self.use_enhanced and 'tool_selection' in analysis:
            ts = analysis['tool_selection']
            print(f"🔧 Tools detectadas: {ts.get('recommended_tools', [])}")
            print(f"💰 Costo estimado: {ts.get('estimated_cost', 'Variable')}")
        
        # Fase 2: Plan
        plan = self.create_plan(analysis)
        print(f"📋 Plan creado: {len(plan)} tareas")
        for task in plan:
            tool_info = f" ([tools: {task.required_tools}])" if task.required_tools else ""
            print(f"   - T{task.id}: {task.agent_type.value}{tool_info}")
        
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
            "plan": [{"id": t.id, "agent": t.agent_type.value, "tools": t.required_tools, "desc": t.description} for t in plan],
            "results": results,
            "final_response": final_response,
            "plugin_stats": self.tool_plugin.get_stats() if self.tool_plugin else None
        }
    
    def _integrate_results(self, results: Dict[str, str], analysis: Dict[str, Any]) -> str:
        """Integrar resultados"""
        parts = ["🎯 Resultado Multi-Agente SWARM:\n"]
        
        for task_id, result in results.items():
            parts.append(f"\n--- {task_id} ---\n{result[:500]}...")
        
        return "\n".join(parts)


# === DEMO ===

def demo_comparison():
    """Compara vanilla vs enhanced"""
    
    test_cases = [
        "Investiga las últimas noticias sobre OpenAI",
        "Crea un script para hacer backup automático",
        "Lee config.json y genera documentación",
        "Genera una imagen de un robot programando",
    ]
    
    print("="*70)
    print("🔦 COMPARACIÓN: Vanilla vs Enhanced with Tool Plugin")
    print("="*70)
    
    for test in test_cases:
        print(f"\n{'='*70}")
        print(f"📥 TAREA: {test}")
        print(f"{'='*70}\n")
        
        # Vanilla
        print("[VANILLA v1.0]")
        vanilla = SWARMCoordinator(tool_plugin_enabled=False)
        result_v = vanilla.analyze_request(test)
        print(f"   Agente: {result_v['recommended_agent']}")
        print(f"   Tools: N/A (sin plugin)")
        
        # Enhanced
        print("\n[ENHANCED v1.1 + Plugin]")
        enhanced = SWARMCoordinator(tool_plugin_enabled=True)
        result_e = enhanced.analyze_request(test)
        print(f"   Agente: {result_e['enhanced_agent_recommendation']['agent']}")
        print(f"   Tools: {result_e['tool_selection']['recommended_tools']}")
        print(f"   Costo: {result_e['tool_selection']['estimated_cost']}")
        if result_e['enhanced_agent_recommendation']['override']:
            print(f"   ⚡ Override aplicado")


if __name__ == "__main__":
    demo_comparison()
