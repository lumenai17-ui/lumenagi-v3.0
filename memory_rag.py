#!/usr/bin/env python3
"""
LumenAGI Vector Memory System
=============================
RAG implementation using nomic-embed-text and ChromaDB.
All local - no external APIs required.
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple

# Configuration
SKILLS_DIR = "/home/lumen/lumenagi-v3.0/skills"
CHROMA_DB_DIR = "/home/lumen/lumenagi-v3.0/chroma_db"
EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1"
SKILL_FILES = [
    "AUTONOMOUS_MODE.md",
    "COORDINATOR_SWARM.md", 
    "DASHBOARD_V4.md",
    "KEEPALIVE_OLLAMA.md",
    "SWARM_ARCHITECTURE_V3.md"
]

class LumenMemory:
    """Vector memory for LumenAGI skills using ChromaDB."""
    
    def __init__(self, persist_dir: str = CHROMA_DB_DIR):
        self.persist_dir = persist_dir
        # Use sentence-transformers to load nomic-embed-text
        print("📦 Loading nomic-embed-text model (384 dims)...")
        self.embedder = SentenceTransformer(
            "nomic-ai/nomic-embed-text-v1",
            trust_remote_code=True
        )
        self.dim = self.embedder.get_sentence_embedding_dimension()
        print(f"✅ Model loaded: {self.dim} dimensions")
        
        # Initialize ChromaDB
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        
    def get_or_create_collection(self, name: str = "skills"):
        """Get or create a collection with cosine similarity."""
        from chromadb.utils.embedding_functions import EmbeddingFunction
        
        class NomicEmbedder(EmbeddingFunction):
            def __init__(self, embedder):
                self.embedder = embedder
            def __call__(self, input: List[str]) -> List[List[float]]:
                # nomic-embed-text uses prefix for documents
                prefixed = [f"search_document: {text}" for text in input]
                embeddings = embedder.embed(prefixed)
                return embeddings.tolist()
        
        embedder = self.embedder
        class EF(EmbeddingFunction):
            def __call__(inner_self, input: List[str]) -> List[List[float]]:
                prefixed = [f"search_document: {text}" for text in input]
                return embedder.encode(prefixed).tolist()
        
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def embed_query(self, query: str) -> List[float]:
        """Embed a query with search prefix (nomic-embed-text convention)."""
        prefixed = f"search_query: {query}"
        return self.embedder.encode(prefixed).tolist()
    
    def load_skills(self, skills_dir: str = SKILLS_DIR) -> int:
        """Load all skill files into ChromaDB."""
        collection = self.get_or_create_collection("skills")
        
        # Clear existing
        existing = collection.get()
        if existing['ids']:
            collection.delete(ids=existing['ids'])
            print(f"🗑️ Cleared {len(existing['ids'])} existing documents")
        
        total_indexed = 0
        
        for filename in SKILL_FILES:
            filepath = os.path.join(skills_dir, filename)
            if not os.path.exists(filepath):
                print(f"⚠️ Skip: {filename} not found")
                continue
                
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create document with prefix for nomic-embed-text
            doc_prefix = f"search_document: {content}"
            embedding = self.embedder.encode(doc_prefix).tolist()
            
            # Extract title from first h1 or use filename
            title = filename.replace('.md', '')
            for line in content.split('\n'):
                if line.startswith('# '):
                    title = line.replace('# ', '').strip()
                    break
            
            # Add to collection with explicit embedding
            collection.add(
                ids=[filename],
                embeddings=[embedding],
                documents=[content],
                metadatas=[{
                    "filename": filename,
                    "title": title,
                    "source": filepath
                }]
            )
            
            print(f"📝 Indexed: {title} ({filename})")
            total_indexed += 1
        
        print(f"\n✅ Total skills indexed: {total_indexed}")
        return total_indexed
    
    def query(self, query_text: str, n_results: int = 3) -> List[Dict]:
        """Query the vector memory for skills."""
        collection = self.client.get_collection("skills")
        
        # Embed query with search_query prefix
        query_embedding = self.embed_query(query_text)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        matches = []
        for i in range(len(results['ids'][0])):
            matches.append({
                "id": results['ids'][0][i],
                "document": results['documents'][0][i][:200] + "...",
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i],
                "similarity_score": 1 - results['distances'][0][i]
            })
        
        return matches


def main():
    """Main execution for testing."""
    print("=" * 60)
    print("LumenAGI Vector Memory System")
    print("=" * 60)
    
    # Initialize memory
    memory = LumenMemory()
    
    # Load skills
    print("\n📚 Loading skills into ChromaDB...")
    memory.load_skills()
    
    # Test query
    test_query = "how to build a dashboard"
    print(f"\n🔍 Test Query: '{test_query}'")
    print("-" * 60)
    
    results = memory.query(test_query, n_results=2)
    
    print(f"\n📊 Top {len(results)} Results:")
    print("-" * 60)
    
    for i, match in enumerate(results, 1):
        print(f"\n#{i}: {match['metadata']['title']}")
        print(f"   File: {match['id']}")
        print(f"   Similarity Score: {match['similarity_score']:.4f}")
        print(f"   Cosine Distance: {match['distance']:.4f}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    
    return results


if __name__ == "__main__":
    main()
