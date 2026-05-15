"""Semantic search over indexed knowledge base."""

import logging

logger = logging.getLogger(__name__)


async def search_knowledge_base(query: str, top_k: int = 5, chroma_path: str = "./chroma_db") -> list[dict]:
    """Search the Tnufa knowledge base for relevant information."""
    try:
        import chromadb

        client = chromadb.PersistentClient(path=chroma_path)
        collection = client.get_collection("tnufa_procedures")

        results = collection.query(query_texts=[query], n_results=top_k)

        docs = []
        for i in range(len(results["documents"][0])):
            docs.append({
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        return docs

    except Exception as e:
        logger.warning(f"Knowledge base search failed: {e}")
        return []
