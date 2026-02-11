#!/usr/bin/env python3
"""
LumenAGI Memory System v1.0
Fase 2: Vector Memory + RAG over Skills

Usa nomic-embed-text para embeddings locales (sin API)
ChromaDB para almacenamiento vectorial local
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("⚠️ sentence-transformers no instalado")

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    CHROMA_AVAILABLE = False
    print("⚠️ chromadb no instalado")


class LumenMemory:
    """
    Sistema de memoria vectorial para LumenAGI
    
    Features:
    - Embeddings locales con nomic-embed-text (384 dims, ~100MB)
    - Almacenamiento ChromaDB local
    - RAG (Retrieval Augmented Generation) sobre skills
    - Búsqueda semántica en documentos
    """
    
    def __init__(self, persist_dir: str = "./memory_db"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(exist_ok=True)
        
        # Inicializar modelo de embeddings (nomic-embed-text)
        # 384 dimensiones, optimizado para retrieval
        print("🧠 Cargando nomic-embed-text...")
        self.model = SentenceTransformer('nomic-ai/nomic-embed-text-v1.5', trust_remote_code=True)
        
        # Inicializar ChromaDB
        print("💾 Inicializando ChromaDB...")
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Colecciones
        self.skills_collection = self.client.get_or_create_collection(
            name="skills",
            metadata={"description": "Documented skills and capabilities"}
        )
        
        self.conversations_collection = self.client.get_or_create_collection(
            name="conversations",
            metadata={"description": "Session transcripts and contexts"}
        )
        
        self.memory_collection = self.client.get_or_create_collection(
            name="memory",
            metadata={"description": "Long-term curated memories"}
        )
        
        print(f"✅ Memory System ready: {self.persist_dir}")
    
    def _generate_id(self, text: str, source: str) -> str:
        """Generar ID único basado en contenido"""
        content = f"{source}:{text[:100]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_skill(self, name: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """
        Agregar un skill al vector store
        
        Args:
            name: Nombre del skill (ej: "DASHBOARD_V4")
            content: Contenido completo del skill
            metadata: Dict con tags, categoria, etc.
        
        Returns:
            ID del documento insertado
        """
        doc_id = self._generate_id(content, f"skill:{name}")
        
        # Generar embedding
        embedding = self.model.encode(content, convert_to_numpy=True).tolist()
        
        # Metadata
        doc_metadata = {
            "type": "skill",
            "name": name,
            "source": f"skills/{name}.md",
            **(metadata or {})
        }
        
        # Insertar
        self.skills_collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content[:8000]],  # Límite de ChromaDB
            metadatas=[doc_metadata]
        )
        
        print(f"💾 Skill '{name}' indexado (ID: {doc_id[:8]}...)")
        return doc_id
    
    def search_skills(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Buscar skills relevantes para una query
        
        Args:
            query: Texto de búsqueda
            n_results: Cuántos resultados retornar
        
        Returns:
            Lista de skills con score de relevancia
        """
        # Generar embedding de la query
        query_embedding = self.model.encode(query, convert_to_numpy=True).tolist()
        
        # Buscar
        results = self.skills_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Formatear resultados
        skills = []
        if results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                skill = {
                    "id": doc_id,
                    "name": results['metadatas'][0][i].get('name', 'unknown'),
                    "content": results['documents'][0][i],
                    "score": 1 - results['distances'][0][i],  # Convertir distancia a score
                    "metadata": results['metadatas'][0][i]
                }
                skills.append(skill)
        
        return skills
    
    def add_conversation(self, session_id: str, messages: List[Dict], summary: str = None):
        """
        Indexar una conversación para RAG futuro
        
        Args:
            session_id: ID único de la sesión
            messages: Lista de mensajes {role, content, timestamp}
            summary: Resumen opcional de la conversación
        """
        # Combinar mensajes en un documento
        conversation_text = "\n".join([
            f"{m.get('role', 'unknown')}: {m.get('content', '')}"
            for m in messages
        ])
        
        if summary:
            conversation_text = f"SUMMARY: {summary}\n\n{conversation_text}"
        
        doc_id = f"conv:{session_id}"
        embedding = self.model.encode(conversation_text, convert_to_numpy=True).tolist()
        
        self.conversations_collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[conversation_text[:8000]],
            metadatas=[{
                "type": "conversation",
                "session_id": session_id,
                "message_count": len(messages)
            }]
        )
        
        print(f"💾 Conversación '{session_id}' indexada")
    
    def search_conversations(self, query: str, n_results: int = 5) -> List[Dict]:
        """Buscar en historial de conversaciones"""
        query_embedding = self.model.encode(query, convert_to_numpy=True).tolist()
        
        results = self.conversations_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        conversations = []
        if results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                conv = {
                    "id": doc_id,
                    "session_id": results['metadatas'][0][i].get('session_id'),
                    "content": results['documents'][0][i],
                    "score": 1 - results['distances'][0][i]
                }
                conversations.append(conv)
        
        return conversations
    
    def rag_query(self, query: str, context_type: str = "skills") -> Dict[str, Any]:
        """
        RAG completo: retrieve + augment + generate context
        
        Args:
            query: Pregunta del usuario
            context_type: 'skills', 'conversations', o 'all'
        
        Returns:
            Dict con contexto recuperado y query mejorada
        """
        context_parts = []
        
        if context_type in ["skills", "all"]:
            skills = self.search_skills(query, n_results=3)
            for skill in skills:
                if skill['score'] > 0.7:  # Umbral de relevancia
                    context_parts.append(f"SKILL: {skill['name']}\n{skill['content'][:500]}")
        
        if context_type in ["conversations", "all"]:
            convs = self.search_conversations(query, n_results=2)
            for conv in convs:
                if conv['score'] > 0.7:
                    context_parts.append(f"PREVIOUS CONTEXT:\n{conv['content'][:300]}")
        
        # Construir contexto
        context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant context found."
        
        return {
            "original_query": query,
            "context": context,
            "sources": [p.split('\n')[0] for p in context_parts],
            "augmented_prompt": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer based on the context above:"
        }
    
    def stats(self) -> Dict[str, Any]:
        """Estadísticas del sistema de memoria"""
        return {
            "skills_count": self.skills_collection.count(),
            "conversations_count": self.conversations_collection.count(),
            "memory_count": self.memory_collection.count(),
            "embedding_model": "nomic-embed-text-v1.5",
            "embedding_dims": 384,
            "persist_dir": str(self.persist_dir)
        }


def index_all_skills(memory: LumenMemory, skills_dir: str = "./skills"):
    """
    Indexar todos los archivos de skills en el directorio
    """
    skills_path = Path(skills_dir)
    if not skills_path.exists():
        print(f"⚠️ Directorio {skills_dir} no existe")
        return
    
    for skill_file in skills_path.glob("*.md"):
        name = skill_file.stem
        content = skill_file.read_text()
        
        # Extraer metadata del markdown
        metadata = {"file_size": len(content)}
        if "## What It Does" in content:
            metadata["has_description"] = True
        if "## Code" in content:
            metadata["has_code"] = True
        
        memory.add_skill(name, content, metadata)
    
    print(f"✅ Indexados {memory.stats()['skills_count']} skills")


# Demo
if __name__ == "__main__":
    print("🚀 LumenAGI Memory System v1.0")
    print("="*50)
    
    # Inicializar
    memory = LumenMemory(persist_dir="./memory_db")
    
    # Indexar skills existentes
    print("\n📚 Indexando skills...")
    index_all_skills(memory, "./skills")
    
    # Demo RAG
    print("\n🔍 Demo RAG Query:")
    query = "how to build a dashboard"
    result = memory.rag_query(query)
    
    print(f"\nQuery: {query}")
    print(f"Sources: {result['sources']}")
    print(f"Context length: {len(result['context'])} chars")
    
    # Stats
    print("\n📊 Stats:")
    stats = memory.stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
