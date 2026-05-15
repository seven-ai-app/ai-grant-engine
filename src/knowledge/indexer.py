"""Index Tnufa knowledge base documents into ChromaDB."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def index_knowledge_base(kb_path: str = "knowledge_base", chroma_path: str = "./chroma_db"):
    """Index all documents in knowledge_base/ into ChromaDB for RAG retrieval."""
    import chromadb

    kb_dir = Path(kb_path)
    if not kb_dir.exists():
        logger.warning(f"Knowledge base directory not found: {kb_dir}")
        return

    client = chromadb.PersistentClient(path=chroma_path)

    # Create or get collection
    collection = client.get_or_create_collection(
        name="tnufa_procedures",
        metadata={"description": "Innovation Authority Tnufa track procedures and rules"},
    )

    documents = []
    metadatas = []
    ids = []

    # Process markdown files
    for md_file in kb_dir.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        chunks = _chunk_document(content, max_chars=1000)

        for i, chunk in enumerate(chunks):
            doc_id = f"{md_file.stem}_{i}"
            documents.append(chunk)
            metadatas.append({
                "source": str(md_file),
                "section": md_file.stem,
                "chunk_index": i,
            })
            ids.append(doc_id)

    if documents:
        collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
        logger.info(f"Indexed {len(documents)} chunks from {kb_dir}")
    else:
        logger.info("No documents found to index")


def _chunk_document(text: str, max_chars: int = 1000) -> list[str]:
    """Split document into chunks at paragraph boundaries."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk += "\n\n" + para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text]
