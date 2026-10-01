import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.models.research import DocumentChunk
from app.core.logging import logger


async def store_document_chunk(
    db: AsyncSession,
    content: str,
    token_count: int,
    source_id: Optional[uuid.UUID] = None,
    learning_module_id: Optional[uuid.UUID] = None,
    chunk_index: int = 0,
    embedding: Optional[List[float]] = None,
    embedding_model: str = "text-embedding-3-small",
    embedding_version: int = 1,
    metadata_json: Optional[Dict[str, Any]] = None,
) -> DocumentChunk:
    """
    Stores an embedded document chunk backed by pgvector (§10, §40).
    Enforces embedding_model and embedding_version tagging for safe similarity search.
    """
    chunk = DocumentChunk(
        id=uuid.uuid4(),
        source_id=source_id,
        learning_module_id=learning_module_id,
        chunk_index=chunk_index,
        content=content,
        token_count=token_count,
        embedding=embedding,
        embedding_model=embedding_model,
        embedding_version=embedding_version,
        metadata_json=metadata_json or {},
    )
    db.add(chunk)
    await db.commit()
    await db.refresh(chunk)
    return chunk


async def search_similar_chunks(
    db: AsyncSession,
    query_embedding: List[float],
    limit: int = 5,
    embedding_model: str = "text-embedding-3-small",
    embedding_version: int = 1,
) -> List[DocumentChunk]:
    """
    Executes cosine distance similarity search against pgvector document_chunks (§10, §40).
    Filters strictly by embedding_model and embedding_version to avoid vector incompatibility.
    """
    stmt = (
        select(DocumentChunk)
        .where(
            DocumentChunk.embedding_model == embedding_model,
            DocumentChunk.embedding_version == embedding_version,
            DocumentChunk.embedding.isnot(None),
        )
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
