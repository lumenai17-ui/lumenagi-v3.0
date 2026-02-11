#!/usr/bin/env python3
"""
LumenAGI SWARM Coordinator v2.0 con Auto-Tool Selection
Arquitectura: Kimi Cerebro + Qwen Agente + Auto-Tools

Mejoras v2.0:
- Auto-tool selection integrado
- Planning con reconocimiento de herramientas necesarias
- Cost estimation antes de ejecución
- Fallback strategies automáticas
"""

import json
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Importar tool selector
sys.path.insert(0, '/home/lumen/.openclaw/workspace')
from coordinator_tool_selector import ToolSelector, ToolExecutor, ToolCategory


class AgentType(Enum):
    """Tipos de agentes disponibles en el SWARM v2"""
    COORDINATOR = "coordinator"      # Kimi K2.5 - decisiones, orquestación
    CODE_LOCAL = "code_local"        # Qwen 32B - código simple, parsing
    RESEARCH = "research"            # GPT-4o - investigación profunda
    CODE_REVIEW = "code_review"      # GPT-4o - revisión/debug
    VISION = "vision"                # APIs - imágenes/video
    BUILD = "build"                  # Qwen 32B - builds, tareas pesadas
    CREATE = "create"                # Qwen 32B - contenido creativo


@dataclass
class SubTask:
    """Una subtarea enriquecida con tool selection"""
    id: str
    agent_type: AgentType
    description: str
    required_tools: List[str]  # Tools que NECESITA usar
    optional_tools: List[str]  # Tools que PODRÍA usar
    estimated_cost: str
    fallback_strategy: str
    input_data: Dict[str, Any]
    max_tokens: int = 1000
    depends_on: List[str] = None
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


class SWARMCoordinatorV2:
    """
    Coordinator v2 con Auto-Tool Selection
    """
    
    AGENT_MODELS = {
        AgentType.COORDINATOR: "ollama/kimi-k2.5:cloud",
        AgentType.CODE_LOCAL: "ollama/qwen2.5:32b",
        AgentType.BUILD: "ollama/qwen2.5:32b",
        AgentType.CREATE: "ollama/qwen2.5:32b",
        AgentType.RESEARCH: "openai/gpt-4o",
        AgentType.CODE_REVIEW: "openai/gpt-4o",
    }
    
    def __init__(self):
        self.tool_selector = ToolSelector()
        self.tool_executor = ToolExecutor(self.tool_selector)
        self.execution_log = []
        
    def analyze_and_plan(self, user_request: str) -> Dict[str, Any]:
        """
        Fase 1-2: Análisis + Selección de tools + Creación de plan
        """
        print(f"🧠 Analizando: \"{user_request[:60]}...\"")
        
        # 1. Clasificar tarea con tool selector
        profile = self.tool_selector.classify_task(user_request)
        print(f"📊 Perfil detectado:")
        print(f"   🌐 Web: {profile.needs_web} | 💻 Código: {profile.needs_code} | 🎮 GPU: {profile.needs_gpu}")
        print(f"   📚 Research: {profile.needs_research} | 📁 Files: {profile.needs_file_io}")
        
        # 2. Obtener plan de ejecución
        plan = self.tool_selector.build_tool_plan(profile)
        print(f"🎯 Agente recomendado: {plan['agent']}")
        print(f"   Razón: {plan['agent_reasoning']}")
        print(f"   💰 Costo estimado: {plan.get('estimated_cost', 'Variable')}")
        
        # 3. Crear subtareas enriquecidas
        return self._create_enriched_plan(user_request, profile, plan)
    
    def _create_enriched_plan(self, user_request: str, profile, plan) -> Dict[str, Any]:
        """Crear plan enriquecido con metadata de tools"""
        
        agent_map = {
            "main": AgentType.COORDINATOR,
            "coordinator": AgentType.COORDINATOR,
            "research": AgentType.RESEARCH,
            "build-qwen32": AgentType.BUILD,
            "build": AgentType.BUILD,
            "create-qwen32": AgentType.CREATE,
            "code_local": AgentType.CODE_LOCAL,
        }
        
        recommended_agent = agent_map.get(plan['agent'], AgentType.COORDINATOR)
        
        # Separar tools requeridas vs opcionales por confianza
        required_tools = [t['tool'] for t in plan['tools'] if t['confidence'] > 0.7]
        optional_tools = [t['tool'] for t in plan['tools'] if 0.3 <= t['confidence'] <= 0.7]
        
        # Detectar si necesita múltiples pasos
        tasks = []
        
        # Paso 1: Research si es necesario
        if profile.needs_research and not profile.needs_code:
            tasks.append(SubTask(
                id="T1",
                agent_type=AgentType.RESEARCH,
                description=f"Investigar: {user_request}",
                required_tools=["web_search", "web_fetch"],
                optional_tools=[],
                estimated_cost="~$0.02 (API)",
                fallback_strategy="Buscar en caché local o preguntar a usuario",
                input_data={"query": user_request},
                max_tokens=2000
            ))
        
        # Paso 2: Ejecución principal con tools
        if profile.needs_code or profile.needs_web or profile.needs_file_io:
            task_deps = ["T1"] if tasks else []
            
            if profile.needs_gpu or profile.needs_code:
                agent_type = AgentType.BUILD
            else:
                agent_type = AgentType.COORDINATOR
            
            tasks.append(SubTask(
                id=f"T{len(tasks)+1}",
                agent_type=agent_type,
                description="Ejecución con tools automáticas",
                required_tools=required_tools,
                optional_tools=optional_tools,
                estimated_cost=plan.get('estimated_cost', 'Variable'),
                fallback_strategy=plan['fallback_strategy'],
                input_data={
                    "request": user_request,
                    "profile": {
                        "needs_research": profile.needs_research,
                        "needs_code": profile.needs_code,
                        "needs_gpu": profile.needs_gpu,
                    }
                },
                max_tokens=1500,
                depends_on=task_deps
            ))
        
        # Si no hay tareas específicas, usar coordinator genérico
        if not tasks:
            tasks.append(SubTask(
                id="T1",
                agent_type=AgentType.COORDINATOR,
                description=user_request,
                required_tools=[],
                optional_tools=[t['tool'] for t in plan['tools']],
                estimated_cost="Variable",
                fallback_strategy="Delegar a sub-agente especializado",
                input_data={"request": user_request},
                max_tokens=1000
            ))
        
        return {
            "original_request": user_request,
            "profile": {
                "needs_research": profile.needs_research,
                "needs_code": profile.needs_code,
                "needs_gpu": profile.needs_gpu,
                "needs_web": profile.needs_web,
                "needs_file_io": profile.needs_file_io,
                "duration": profile.estimated_duration,
            },
            "execution_plan": plan,
            "tasks": tasks,
            "ready_to_execute": True,
            "human_approval_needed": plan.get('requires_human_check', False)
        }
    
    def execute_task_v2(self, task: SubTask) -> Dict[str, Any]:
        """
        Fase 3: Ejecutar con metadata de tools
        """
        model = self.AGENT_MODELS[task.agent_type]
        
        # Construir prompt enriquecido con tools disponibles
        prompt = self._build_enriched_prompt(task)
        
        print(f"⚡ Ejecutando {task.id} con {task.agent_type.value}")
        print(f"   🔧 Tools: {', '.join(task.required_tools) if task.required_tools else 'Ninguna'}")
        print(f"   💰 Costo: {task.estimated_cost}")
        
        # Simular ejecución (en producción, llamaría al modelo real)
        execution_result = f"""
[Simulación] Agent: {task.agent_type.value}
Model: {model}
Task: {task.description[:50]}...
Tools disponibles: {task.required_tools}
Prompt length: {len(prompt)} chars
Max tokens: {task.max_tokens}
        """.strip()
        
        # Log de ejecución
        self.execution_log.append({
            "task_id": task.id,
            "agent": task.agent_type.value,
            "tools_used": task.required_tools,
            "cost": task.estimated_cost,
            "result_preview": execution_result[:200]
        })
        
        return {
            "status": "completed",
            "task_id": task.id,
            "agent": task.agent_type.value,
            "result": execution_result,
            "tools_intended": task.required_tools,
            "actual_tokens_used": "~estimated",
        }
    
    def _build_enriched_prompt(self, task: SubTask) -> str:
        """Prompt enriquecido con información de tools"""
        
        tool_instructions = []
        
        for tool in task.required_tools:
            instructions = {
                "web_search": "Usa web_search para encontrar información actualizada",
                "web_fetch": "Usa web_fetch para extraer contenido de URLs específicas",
                "code_exec": "Ejecuta código Python con code_exec (sandbox seguro)",
                "file_read": "Lee archivos con file_read para acceder a datos",
                "file_write": "Guarda resultados con file_write",
                "telegram": "Envía notificaciones con telegram",
            }.get(tool, f"Usa {tool} cuando sea necesario")
            tool_instructions.append(f"- {instructions}")
        
        tools_section = "\n".join(tool_instructions) if tool_instructions else "Sin tools específicas requeridas."
        
        return f"""Eres un agente del sistema SWARM LumenAGI.

TAREA: {task.description}

TOOLS DISPONIBLES PARA ESTA TAREA:
{tools_section}

INSTRUCCIONES:
1. Analiza la tarea y usa las tools disponibles automáticamente
2. Si necesitas información externa → usa web_search
3. Si necesitas ejecutar código → usa code_exec
4. Reporta progreso y resultados claramente

OUTPUT ESPERADO:
{task.agent_type.value.upper()} result here...
"""
    
    def run_v2(self, user_request: str, auto_execute: bool = True) -> Dict[str, Any]:
        """
        Entry point principal v2
        """
        print("="*70)
        print("🦀 LUMENAGI SWARM COORDINATOR v2.0")
        print("   Con Auto-Tool Selection")
        print("="*70)
        
        # Fase 1-2: Análisis y Plan
        plan_result = self.analyze_and_plan(user_request)
        
        print(f"\n📋 Plan creado: {len(plan_result['tasks'])} subtareas")
        for task in plan_result['tasks']:
            print(f"   → {task.id}: {task.agent_type.value} | Tools: {len(task.required_tools)} | {task.estimated_cost}")
        
        # Si requiere aprobación humana, preguntar
        if plan_result.get('human_approval_needed'):
            print("\n⚠️  ALTA INCERTIDUMBRE: Algunas tools tienen baja confianza")
            print("   ¿Proceder? (En modo auto, asumiendo SÍ)")
        
        # Fase 3: Ejecución (si auto_execute)
        if auto_execute:
            print("\n🚀 Ejecutando plan...")
            execution_results = []
            for task in plan_result['tasks']:
                result = self.execute_task_v2(task)
                execution_results.append(result)
                print(f"   ✅ {task.id} completado")
        else:
            execution_results = []
            print("\n⏸️  Ejecución pausada (auto_execute=False)")
        
        # Resumen final
        print("\n" + "="*70)
        print("📊 RESUMEN DE EJECUCIÓN")
        print("="*70)
        print(f"Tareas ejecutadas: {len(execution_results)}")
        print(f"Costo total estimado: {sum(self._parse_cost(r.get('cost', '0')) for r in execution_results)}")
        
        return {
            "request": user_request,
            "plan": plan_result,
            "execution_results": execution_results,
            "log": self.execution_log,
            "status": "completed" if auto_execute else "planned"
        }
    
    def _parse_cost(self, cost_str: str) -> float:
        """Parse simple de costo estimado"""
        try:
            if "FREE" in cost_str:
                return 0.0
            import re
            match = re.search(r'\$([0-9.]+)', cost_str)
            return float(match.group(1)) if match else 0.0
        except:
            return 0.0


# === DEMO ===

def demo_v2():
    """Demostración del Coordinator v2 con Auto-Tool Selection"""
    coordinator = SWARMCoordinatorV2()
    
    test_cases = [
        "Investiga las últimas tendencias en LLMs locales y resume los hallazgos",
        "Crea un script de Python que haga web scraping de Hacker News",
        "Lee el archivo de configuración config.yaml y genera documentación",
        "Debug este código que falla: def factorial(n): return n * factorial(n-1)",
        "Automatiza el envío de reportes semanales por Telegram",
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"TEST #{i}: {test}")
        print('='*70)
        
        result = coordinator.run_v2(test, auto_execute=False)  # Solo planear, no ejecutar
        
        print(f"\n📝 Resultado del planning:")
        print(f"   Ready to execute: {result['plan']['ready_to_execute']}")
        print(f"   Human approval needed: {result['plan'].get('human_approval_needed', False)}")


if __name__ == "__main__":
    demo_v2()
