# RAG Integration v1.0

Retrieval Augmented Generation para LumenAGI SWARM.

## Qué hace

El coordinator consulta memoria vectorial antes de responder:
1. Tarea llega al coordinator
2. RAG busca skills relevantes
3. Contexto agregado al prompt
4. Agente responde con conocimiento institucional

## Archivos

- `memory_system.py` — Core vectorial (ChromaDB + nomic-embed-text)
- `coordinator_rag_plugin.py` — Plugin para coordinator
- `memory_db/` — Base de datos vectorial local

## Uso

```python
from coordinator_rag_plugin import enrich_with_rag

# En el coordinator:
result = enrich_with_rag("Cómo configuro keep-alive?", context_type="skills")

if result['rag_applied']:
    print(f"Contexto: {result['sources']}")
    task_enriquecida = result['enriched_task']
else:
    task_enriquecida = result['original_task']
```

## Indexación de Skills

```python
from memory_system import LumenMemory, index_all_skills

memory = LumenMemory(persist_dir="./memory_db")
index_all_skills(memory, "./skills")
```

## Requisitos

```bash
pip install sentence-transformers>=2.2.0 chromadb>=0.4.0
```

## Primera ejecución

Descarga automática:
- nomic-embed-text-v1.5 (~100MB)
- Inicializa ChromaDB en `./memory_db/`

## Performance

- Búsqueda: ~50ms para 1000 documentos
- Embedding: ~100ms por query
- Todo local, sin API calls

---
*Creado: 2026-02-11 | Modelo: descargando*
