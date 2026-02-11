#!/usr/bin/env python3
"""
RAG Plugin para Coordinator v1.0
Integra LumenMemory (vector RAG) con el coordinator

El coordinator consulta skills/memoria antes de responder
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

try:
    from memory_system import LumenMemory
    MEMORY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Memory system no disponible: {e}")
    MEMORY_AVAILABLE = False


class CoordinatorRAGPlugin:
    """
    Plugin que agrega Retrieval Augmented Generation al coordinator
    Consulta memoria vectorial antes de procesar tareas
    """
    
    def __init__(self, memory_dir: str = "./memory_db", auto_init: bool = False):
        self.memory = None
        self.memory_dir = memory_dir
        self.available = False
        
        if auto_init and MEMORY_AVAILABLE:
            self._init_memory()
    
    def _init_memory(self):
        """Inicializar memoria si está disponible"""
        try:
            print("🧠 Inicializando RAG Memory...")
            self.memory = LumenMemory(persist_dir=self.memory_dir)
            self.available = True
            print(f"✅ RAG ready: {self.memory.stats()['skills_count']} skills indexados")
        except Exception as e:
            print(f"⚠️ RAG init failed: {e}")
            self.available = False
    
    def enrich_task_with_context(self, task: str, context_type: str = "skills") -> Dict:
        """
        Enriquecer una tarea con contexto recuperado de la memoria
        
        Returns:
            Dict con task original, contexto recuperado, y task mejorada
        """
        if not self.available or not self.memory:
            return {
                "original_task": task,
                "context": None,
                "sources": [],
                "enriched_task": task,
                "rag_applied": False,
                "reason": "Memory not available"
            }
        
        try:
            # Hacer RAG query
            rag_result = self.memory.rag_query(task, context_type=context_type)
            
            # Solo usar contexto si hay sources relevantes
            if rag_result['sources']:
                enriched = self._build_enriched_task(task, rag_result)
                return {
                    "original_task": task,
                    "context": rag_result['context'],
                    "sources": rag_result['sources'],
                    "enriched_task": enriched,
                    "rag_applied": True,
                    "confidence": self._estimate_confidence(rag_result)
                }
            else:
                return {
                    "original_task": task,
                    "context": None,
                    "sources": [],
                    "enriched_task": task,
                    "rag_applied": False,
                    "reason": "No relevant skills found"
                }
                
        except Exception as e:
            return {
                "original_task": task,
                "context": None,
                "sources": [],
                "enriched_task": task,
                "rag_applied": False,
                "reason": f"RAG error: {str(e)}"
            }
    
    def _build_enriched_task(self, task: str, rag_result: Dict) -> str:
        """Construir tarea enriquecida con contexto"""
        context = rag_result['context']
        
        enriched = f"""CONTEXTO RELEVANTE DE SKILLS:
{context}

---

TAREA ACTUAL:
{task}

---

INSTRUCCIONES:
1. Usa el contexto de arriba si es relevante para la tarea
2. Si no aplica, procede normalmente
3. Prioriza información de skills sobre conocimiento general
"""
        return enriched
    
    def _estimate_confidence(self, rag_result: Dict) -> float:
        """Estimar confianza del RAG result"""
        if not rag_result.get('sources'):
            return 0.0
        # Más sources = mayor confianza (hasta un punto)
        return min(0.5 + (len(rag_result['sources']) * 0.15), 0.95)
    
    def index_new_skill(self, name: str, content: str, metadata: Dict = None):
        """Indexar un nuevo skill en la memoria"""
        if self.available and self.memory:
            try:
                self.memory.add_skill(name, content, metadata)
                return True
            except Exception as e:
                print(f"⚠️ Error indexing skill: {e}")
        return False
    
    def get_stats(self) -> Dict:
        """Estadísticas del sistema RAG"""
        if self.available and self.memory:
            return {
                "available": True,
                **self.memory.stats()
            }
        return {"available": False, "reason": "Memory not initialized"}


# Función de conveniencia para integración
def enrich_with_rag(task: str, context_type: str = "skills", 
                     memory_dir: str = "./memory_db") -> Dict:
    """
    Función simple para enriquecer una tarea con RAG
    Usar desde el coordinator
    """
    plugin = CoordinatorRAGPlugin(memory_dir=memory_dir, auto_init=True)
    return plugin.enrich_task_with_context(task, context_type)


# Demo
if __name__ == "__main__":
    print("="*60)
    print("🔍 COORDINATOR RAG PLUGIN v1.0 Demo")
    print("="*60)
    
    plugin = CoordinatorRAGPlugin(auto_init=True)
    
    test_tasks = [
        "How do I create a new dashboard widget?",
        "Explícame cómo funciona el sistema de notificaciones",
        "Cómo configuro el keep-alive de Qwen?",
        "Debug this Python error",
    ]
    
    for task in test_tasks:
        print(f"\n📝 Task: {task}")
        result = plugin.enrich_task_with_context(task)
        
        if result['rag_applied']:
            print(f"   ✅ RAG aplicado")
            print(f"   📚 Sources: {result['sources']}")
            print(f"   🎯 Confianza: {result['confidence']:.2f}")
            print(f"   📏 Context: {len(result['context'])} chars")
        else:
            print(f"   ⚠️  RAG no aplicado: {result['reason']}")
    
    print(f"\n📊 Stats: {plugin.get_stats()}")
    print("="*60)
