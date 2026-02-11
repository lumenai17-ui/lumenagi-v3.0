#!/usr/bin/env python3
"""
Coordinator Tool Plugin v1.0 — Integración gradual con SWARM existente
Se conecta al coordinator actual sin reemplazarlo
"""

import sys
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from coordinator_tool_selector import ToolSelector, ToolCategory


class CoordinatorToolPlugin:
    """
    Plugin que agrega tool selection al coordinator existente
    Sin modificar el core — se conecta como extensión
    """
    
    def __init__(self, coordinator=None):
        self.selector = ToolSelector()
        self.coordinator = coordinator
        self.usage_stats = {
            'tasks_analyzed': 0,
            'tools_suggested': 0,
            'acceptance_rate': 1.0
        }
        
    def enhance_task_analysis(self, user_request: str, original_analysis: Dict) -> Dict:
        """
        Mejora el análisis del coordinator existente con tool detection
        
        Input: análisis del coordinator original
        Output: análisis enriquecido con tools recomendadas
        """
        self.usage_stats['tasks_analyzed'] += 1
        
        # Detectar tools
        profile = self.selector.classify_task(user_request)
        plan = self.selector.build_tool_plan(profile)
        
        # Enriquecer análisis original
        enhanced = {
            **original_analysis,
            'tool_selection': {
                'recommended_tools': [t['tool'] for t in plan['tools']],
                'tool_confidence': {t['tool']: t['confidence'] for t in plan['tools']},
                'requires_web': profile.needs_web,
                'requires_files': profile.needs_file_io,
                'requires_execution': profile.needs_code,
                'estimated_cost': plan.get('estimated_cost', 'Variable'),
                'fallback_strategy': plan['fallback_strategy']
            },
            'enhanced_agent_recommendation': self._enhance_agent_choice(
                original_analysis, profile, plan
            )
        }
        
        self.usage_stats['tools_suggested'] += len(plan['tools'])
        
        return enhanced
    
    def _enhance_agent_choice(self, original: Dict, profile, plan) -> Dict:
        """Mejora la recomendación de agente basada en tools"""
        
        # Mapeo de herramientas a preferencia de agente
        tool_preferences = {
            ToolCategory.GPU_COMPUTE: ('build-qwen32', 'GPU local requerido'),
            ToolCategory.CODE_EXEC: ('build-qwen32', 'Ejecución local segura'),
            ToolCategory.IMAGE: ('create-qwen32', 'Generación creativa'),
            ToolCategory.WEB_SEARCH: ('research', 'Research tiene mejor contexto web'),
            ToolCategory.WEB_FETCH: ('research', 'Extracción de datos externa'),
            ToolCategory.BROWSER: ('main', 'Automatización UI requiere coordinación'),
        }
        
        # Revisar si alguna tool high-priority indica agente específico
        for tool_req in profile.tools:
            if tool_req.tool in tool_preferences and tool_req.confidence > 0.7:
                agent_id, reason = tool_preferences[tool_req.tool]
                return {
                    'agent': agent_id,
                    'reason': f"[Plugin] {reason}",
                    'override': True,
                    'original': original.get('recommended_agent', 'unknown'),
                    'confidence': tool_req.confidence
                }
        
        # Si no hay override, mantener recomendación original
        return {
            'agent': plan['agent'],
            'reason': f"[Plugin] {plan['agent_reasoning']}",
            'override': False,
            'original': original.get('recommended_agent', plan['agent']),
            'confidence': 0.7
        }
    
    def get_tool_instructions(self, tools: List[str]) -> str:
        """
        Genera instrucciones para el agente sobre qué tools usar
        El agente recibe esto como contexto adicional
        """
        instructions = [
            "\n🔧 HERRAMIENTAS DISPONIBLES PARA ESTA TAREA:\n",
        ]
        
        tool_help = {
            'web_search': "Usa web_search() para encontrar información actualizada en internet",
            'web_fetch': "Usa web_fetch() para extraer contenido específico de URLs",
            'file_read': "Usa read() para leer archivos necesarios",
            'file_write': "Usa write() para guardar resultados en archivos",
            'code_exec': "Usa exec() para ejecutar código Python de forma segura",
            'telegram': "Usa telegram para enviar notificaciones o mensajes",
            'browser': "Usa browser() para automatización de UI web",
            'github': "Usa github para operaciones de git (commit, push, PR)",
            'image': "Usa image() para generación de imágenes",
            'tts': "Usa tts() para convertir texto a voz"
        }
        
        for tool in tools:
            help_text = tool_help.get(tool, f"Usa {tool}() cuando sea necesario")
            instructions.append(f"  • {help_text}")
        
        instructions.append("\n💡 Elige la herramienta apropiada automáticamente según necesites.")
        
        return "\n".join(instructions)
    
    def suggest_execution_plan(self, task: str, enhanced_analysis: Dict) -> Dict:
        """
        Sugiere un plan de ejecución paso a paso
        """
        tools = enhanced_analysis['tool_selection']['recommended_tools']
        agent = enhanced_analysis['enhanced_agent_recommendation']['agent']
        
        plan = {
            'steps': [],
            'estimated_time': self._estimate_time(tools),
            'risk_level': self._assess_risk(tools),
            'cost_estimate': enhanced_analysis['tool_selection']['estimated_cost']
        }
        
        # Paso 1: Research si es necesario
        if 'web_search' in tools:
            plan['steps'].append({
                'order': 1,
                'action': 'gather_information',
                'tool': 'web_search',
                'description': 'Buscar información relevante en internet'
            })
        
        # Paso 2: File operations
        if 'file_read' in tools:
            plan['steps'].append({
                'order': len(plan['steps']) + 1,
                'action': 'read_context',
                'tool': 'file_read',
                'description': 'Leer archivos de contexto necesarios'
            })
        
        # Paso 3: Main execution
        plan['steps'].append({
            'order': len(plan['steps']) + 1,
            'action': 'execute_main_task',
            'agent': agent,
            'description': f'Ejecutar tarea principal con agente {agent}',
            'tools_available': tools
        })
        
        # Paso 4: Output
        if 'file_write' in tools:
            plan['steps'].append({
                'order': len(plan['steps']) + 1,
                'action': 'save_results',
                'tool': 'file_write',
                'description': 'Guardar resultados en archivo'
            })
        
        return plan
    
    def _estimate_time(self, tools: List[str]) -> str:
        """Estima tiempo basado en tools"""
        if 'web_search' in tools and len(tools) > 3:
            return "2-5 minutos"
        if 'code_exec' in tools:
            return "30 segundos - 2 minutos"
        return "Menos de 30 segundos"
    
    def _assess_risk(self, tools: List[str]) -> str:
        """Evalúa riesgo de la ejecución"""
        high_risk = ['code_exec', 'github', 'browser']
        if any(t in tools for t in high_risk):
            return "medium" if 'github' in tools else "low"
        return "very_low"
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas de uso del plugin"""
        return {
            **self.usage_stats,
            'avg_tools_per_task': (
                self.usage_stats['tools_suggested'] / max(1, self.usage_stats['tasks_analyzed'])
            )
        }


# === FUNCIÓN DE INTEGRACIÓN ===

def enhance_swarm_coordinator(coordinator_instance, task_analysis_result: Dict, user_request: str) -> Dict:
    """
    Función de conveniencia para integrar con coordinator existente
    
    Uso:
        from coordinator_tool_plugin import enhance_swarm_coordinator
        
        # En tu coordinator:
        analysis = analyze_request(user_input)
        enhanced = enhance_swarm_coordinator(self, analysis, user_input)
        # enhanced ahora tiene tool_selection + execution_plan
    """
    plugin = CoordinatorToolPlugin(coordinator_instance)
    enhanced = plugin.enhance_task_analysis(user_request, task_analysis_result)
    enhanced['execution_plan'] = plugin.suggest_execution_plan(user_request, enhanced)
    enhanced['tool_instructions'] = plugin.get_tool_instructions(
        enhanced['tool_selection']['recommended_tools']
    )
    return enhanced


# === DEMO ===

def demo_plugin_integration():
    """Demo de cómo se integra el plugin"""
    plugin = CoordinatorToolPlugin()
    
    # Simular análisis del coordinator original
    test_cases = [
        ("Investiga OpenAI y resume findings", {'needs_research': True, 'recommended_agent': 'research'}),
        ("Crea script de web scraping", {'needs_code': True, 'recommended_agent': 'code_local'}),
        ("Lee config.yaml y genera docs", {'needs_file': True, 'recommended_agent': 'main'}),
    ]
    
    print("="*70)
    print("🔌 COORDINATOR TOOL PLUGIN — Integración Demo")
    print("="*70)
    
    for user_request, original_analysis in test_cases:
        print(f"\n📥 Input: {user_request}")
        print(f"   Análisis original: agent={original_analysis.get('recommended_agent', 'unknown')}")
        
        # Aplicar plugin
        enhanced = plugin.enhance_task_analysis(user_request, original_analysis)
        
        print(f"   🔧 Tools detectadas: {enhanced['tool_selection']['recommended_tools']}")
        print(f"   🤖 Agente enhanced: {enhanced['enhanced_agent_recommendation']['agent']}")
        if enhanced['enhanced_agent_recommendation']['override']:
            print(f"   ⚠️  Override aplicado por tool confidence")
        
        # Mostrar execution plan
        plan = plugin.suggest_execution_plan(user_request, enhanced)
        print(f"   📋 Plan ({plan['estimated_time']}):")
        for step in plan['steps']:
            print(f"      {step['order']}. {step['description']}")
    
    print(f"\n📊 Stats: {plugin.get_stats()}")
    print("="*70)


if __name__ == "__main__":
    demo_plugin_integration()
