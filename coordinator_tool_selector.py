"""
Auto-Tool Selector para LumenAGI SWARM
Clasifica tareas y selecciona automáticamente qué tools usar

Autonomía nivel 2: No solo elige agente, también elige tools específicas
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ToolCategory(Enum):
    """Categorías de herramientas disponibles"""
    WEB_SEARCH = "web_search"
    WEB_FETCH = "web_fetch"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    CODE_EXEC = "code_exec"
    BROWSER = "browser"
    GITHUB = "github"
    TELEGRAM = "telegram"
    IMAGE = "image"
    TTS = "tts"
    GPU_COMPUTE = "gpu_compute"


@dataclass
class ToolRequirement:
    """Requisito de tool para una tarea"""
    tool: ToolCategory
    confidence: float  # 0.0 - 1.0
    reason: str
    priority: int  # 1 = alta, 3 = baja


@dataclass
class TaskProfile:
    """Perfil completo de una tarea"""
    task: str
    needs_research: bool
    needs_code: bool
    needs_gpu: bool
    needs_web: bool
    needs_file_io: bool
    estimated_duration: str  # "short", "medium", "long"
    tools: List[ToolRequirement]


class ToolSelector:
    """
    Selector inteligente de tools basado en análisis de intención
    """

    # Patrones de detección por categoría
    PATTERNS = {
        ToolCategory.WEB_SEARCH: [
            r"\b(buscar|investigar|encontrar|busca|research|search|look up|find)\b",
            r"\b(información sobre|info de|qué es|cómo funciona|latest|news)\b",
            r"\b(actualidad|tendencias|trends|reciente|202[4-9])\b",
        ],
        ToolCategory.WEB_FETCH: [
            r"\b(leer|extraer|contenido de|contenido de la web|scrape|fetch)\b",
            r"\b(url|https?://|www\.|extrae de|resume esta página)\b",
            r"\b(artículo|página web|documentación|docs)\b",
        ],
        ToolCategory.CODE_EXEC: [
            r"\b(ejecutar|correr|testear|probar|run|execute|test)\b",
            r"\b(python|bash|script|código|code|programa|programar)\b",
            r"\b(crear archivo|genera script|write code|implementa)\b",
            r"\b(http server|api|endpoint|fastapi|flask|servidor)\b",
        ],
        ToolCategory.FILE_READ: [
            r"\b(leer archivo|muestra archivo|ver contenido|cat |head |tail )\b",
            r"\b(qué dice|contenido de|lee el archivo|read file)\b",
            r"\b(\w+\.(py|js|json|md|txt|yaml|yml|sh))\b",
        ],
        ToolCategory.FILE_WRITE: [
            r"\b(guardar|escribir|crear archivo|nuevo archivo|write|save)\b",
            r"\b(genera un|crea un|haz un|build|create file)\b",
            r"\b(script|módulo|clase|función|configuración)\b",
        ],
        ToolCategory.BROWSER: [
            r"\b(navegar|browser|automatizar|click|screenshot|página)\b",
            r"\b(ui|interfaz|formulario|login|automation|testing web)\b",
        ],
        ToolCategory.GITHUB: [
            r"\b(git|github|commit|push|pull|repo|repositorio|branch|pr)\b",
            r"\b(subir cambios|guardar en git|version control)\b",
        ],
        ToolCategory.TELEGRAM: [
            r"\b(telegram|enviar mensaje|notificar|mensaje a)\b",
            r"\b(avisa|notifica|send message|broadcast)\b",
        ],
        ToolCategory.IMAGE: [
            r"\b(imagen|genera imagen|dibuja|create image|flux|sdxl)\b",
            r"\b(foto|picture|visual|diagram|chart|generar foto)\b",
        ],
        ToolCategory.TTS: [
            r"\b(voz|hablar|audio|reproducir|text to speech|tts|lee esto)\b",
            r"\b(narrar|cuéntame como historia|voice|speak)\b",
        ],
        ToolCategory.GPU_COMPUTE: [
            r"\b(entrenar|training|fine.?tune|modelo grande|batch processing)\b",
            r"\b(cuda|gpu intensive|procesamiento pesado|video editing)\b",
        ],
    }

    # Keywords que indican duración estimada
    DURATION_PATTERNS = {
        "short": [r"\b(rápido|quick|simple|fácil|easy|ahora|now|ya)\b"],
        "long": [r"\b(investiga a fondo|deep research|implementa completo|full implementation)\b",
                r"\b(análisis exhaustivo|documenta todo|comprehensive)\b"],
    }

    def __init__(self):
        self.compiled_patterns = {
            tool: [re.compile(p, re.IGNORECASE) for p in patterns]
            for tool, patterns in self.PATTERNS.items()
        }
        self.duration_patterns = {
            dur: [re.compile(p, re.IGNORECASE) for p in patterns]
            for dur, patterns in self.DURATION_PATTERNS.items()
        }

    def classify_task(self, task: str) -> TaskProfile:
        """
        Clasifica una tarea y determina qué tools necesita
        """
        task_lower = task.lower()
        tools_detected = []

        # Detectar tools necesarias
        for tool, patterns in self.compiled_patterns.items():
            confidence = 0.0
            matched_patterns = 0
            for pattern in patterns:
                if pattern.search(task_lower):
                    matched_patterns += 1
                    confidence += 0.3  # Cada match añade confianza

            if matched_patterns > 0:
                confidence = min(confidence, 0.95)  # Cap en 0.95
                priority = 2 if confidence > 0.6 else 3
                if confidence > 0.8:
                    priority = 1

                tools_detected.append(ToolRequirement(
                    tool=tool,
                    confidence=confidence,
                    reason=f"Detectado '{tool.value}' en tarea ({matched_patterns} matches)",
                    priority=priority
                ))

        # Ordenar por prioridad y confianza
        tools_detected.sort(key=lambda x: (x.priority, -x.confidence))

        # Determinar flags generales
        needs_research = any(t.tool in [ToolCategory.WEB_SEARCH, ToolCategory.WEB_FETCH] for t in tools_detected)
        needs_code = any(t.tool in [ToolCategory.CODE_EXEC, ToolCategory.FILE_WRITE, ToolCategory.GITHUB] for t in tools_detected)
        needs_gpu = any(t.tool == ToolCategory.GPU_COMPUTE for t in tools_detected) or "qwen" in task_lower
        needs_web = any(t.tool in [ToolCategory.WEB_SEARCH, ToolCategory.WEB_FETCH, ToolCategory.BROWSER] for t in tools_detected)
        needs_file_io = any(t.tool in [ToolCategory.FILE_READ, ToolCategory.FILE_WRITE] for t in tools_detected)

        # Estimar duración
        estimated_duration = "medium"
        for pattern in self.duration_patterns["short"]:
            if pattern.search(task_lower):
                estimated_duration = "short"
                break
        for pattern in self.duration_patterns["long"]:
            if pattern.search(task_lower):
                estimated_duration = "long"
                break

        # Si no detectamos tools específicas, inferir del contexto general
        if not tools_detected:
            # Tareas de investigación general
            if any(kw in task_lower for kw in ["investiga", "research", "busca", "qué es", "cómo"]):
                tools_detected.append(ToolRequirement(
                    tool=ToolCategory.WEB_SEARCH,
                    confidence=0.7,
                    reason="Tarea tipo investigación general",
                    priority=1
                ))
                needs_research = True

        return TaskProfile(
            task=task,
            needs_research=needs_research,
            needs_code=needs_code,
            needs_gpu=needs_gpu,
            needs_web=needs_web,
            needs_file_io=needs_file_io,
            estimated_duration=estimated_duration,
            tools=tools_detected
        )

    def recommend_agent(self, profile: TaskProfile) -> Tuple[str, str]:
        """
        Recomienda qué agente usar basado en el perfil
        Returns: (agent_id, reasoning)
        """
        # Reglas de routing
        if profile.needs_gpu and profile.needs_code:
            return ("build-qwen32", "Código + GPU disponible = Qwen 32B local óptimo")

        if profile.needs_research and not profile.needs_code:
            return ("research", "Investigación pura = GPT-4o para máxima calidad")

        if profile.needs_code and not profile.needs_gpu:
            return ("build-qwen32", "Código simple = Qwen rápido y económico")

        if any(t.tool == ToolCategory.BROWSER for t in profile.tools):
            return ("main", "Automatización UI requiere coordinación")

        if any(t.tool == ToolCategory.IMAGE for t in profile.tools):
            return ("create-qwen32", "Generación de imágenes = agente creativo")

        # Default al cerebro
        return ("main", "Tarea ambigua o compleja = coordinador decide")

    def build_tool_plan(self, profile: TaskProfile) -> Dict:
        """
        Construye un plan de ejecución con las tools seleccionadas
        """
        agent_id, reasoning = self.recommend_agent(profile)

        # Seleccionar tools que realmente usaremos (top 3 por confianza)
        selected_tools = profile.tools[:3]

        # Construir plan
        plan = {
            "agent": agent_id,
            "agent_reasoning": reasoning,
            "estimated_duration": profile.estimated_duration,
            "tools": [
                {
                    "tool": t.tool.value,
                    "confidence": round(t.confidence, 2),
                    "reason": t.reason,
                    "order": i + 1
                }
                for i, t in enumerate(selected_tools)
            ],
            "fallback_strategy": self._determine_fallback(profile),
            "requires_human_check": any(t.confidence < 0.6 for t in selected_tools)
        }

        return plan

    def _determine_fallback(self, profile: TaskProfile) -> str:
        """Determina estrategia de fallback si tools fallan"""
        if profile.needs_web:
            return "Si web_search falla: usar web_fetch con URLs alternativas"
        if profile.needs_code:
            return "Si ejecución falla: mostrar código para revisión manual"
        return "Si todo falla: preguntar a usuario para clarificación"


class ToolExecutor:
    """
    Ejecutor que usa el plan de tools seleccionado
    """

    def __init__(self, selector: ToolSelector):
        self.selector = selector
        self.execution_log = []

    def execute_with_plan(self, task: str, context: Optional[Dict] = None) -> Dict:
        """
        Ejecuta una tarea con selección automática de tools
        """
        # Paso 1: Clasificar
        profile = self.selector.classify_task(task)

        # Paso 2: Construir plan
        plan = self.selector.build_tool_plan(profile)

        # Paso 3: Log
        self.execution_log.append({
            "task": task,
            "plan": plan,
            "timestamp": "now",
            "context": context
        })

        # Retornar plan para ejecución (el agente real ejecuta)
        return {
            "status": "planned",
            "task": task,
            "execution_plan": plan,
            "alternative_agents": self._suggest_alternatives(profile),
            "estimated_cost": self._estimate_cost(plan),
            "ready_to_execute": True
        }

    def _suggest_alternatives(self, profile: TaskProfile) -> List[str]:
        """Sugiere agentes alternativos"""
        alternatives = []
        if profile.needs_code:
            alternatives.append("build-qwen32 (código local)")
            alternatives.append("research (código cloud)")
        if profile.needs_research:
            alternatives.append("research (GPT-4o)")
        return alternatives

    def _estimate_cost(self, plan: Dict) -> str:
        """Estima costo monetario/computacional"""
        agent = plan["agent"]
        if "qwen" in agent:
            return "FREE (Qwen 32B local)"
        if agent == "research":
            return "~$0.01-0.05 (API cost)"
        return "Variable"


# === EJEMPLOS DE USO ===

def demo():
    """Demo del selector de tools"""
    selector = ToolSelector()
    executor = ToolExecutor(selector)

    test_tasks = [
        "Investiga las últimas noticias sobre IA generativa",
        "Crea un script de Python que haga web scraping de noticias",
        "Lee el archivo config.yaml y muestra su contenido",
        "Genera una imagen de un gato astronauta en el espacio",
        "Ejecuta este código: print('Hello World')",
        "Envía un mensaje a Telegram avisando que terminé",
        "Automatiza el login en una página web",
        "Entrena un modelo de clasificación con este dataset",
    ]

    print("=" * 70)
    print("🦀 AUTO-TOOL SELECTOR DEMO")
    print("=" * 70)

    for task in test_tasks:
        result = executor.execute_with_plan(task)
        plan = result["execution_plan"]

        print(f"\n📝 Tarea: {task}")
        print(f"🤖 Agente: {plan['agent']} ({plan['agent_reasoning']})")
        print(f"⏱️  Duración estimada: {plan['estimated_duration']}")
        print(f"💰 Costo: {result['estimated_cost']}")
        print(f"🔧 Tools seleccionadas:")
        for tool in plan['tools']:
            print(f"   {tool['order']}. {tool['tool']} (conf: {tool['confidence']}) - {tool['reason']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo()
