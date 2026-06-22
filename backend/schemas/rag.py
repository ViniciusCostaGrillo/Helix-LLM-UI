from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    prompt: str = Field(
        ..., description="User's query prompt to run semantic retrieval against"
    )
    collection_name: Optional[str] = Field(
        None, description="Optional target ChromaDB collection (pages, components, styles). Searches all by default."
    )
    limit: int = Field(
        3, ge=1, le=50, description="Top-K context matching results to retrieve"
    )


class RetrievedDocument(BaseModel):
    id: str = Field(
        ..., description="Unique ID of the retrieved document"
    )
    collection: str = Field(
        ..., description="Name of the ChromaDB collection where it was found"
    )
    document: str = Field(
        ..., description="The semantic text body or source code retrieved"
    )
    distance: float = Field(
        ..., description="Similarity distance score (smaller means higher similarity)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata dictionary associated with the matched vector"
    )


class RAGQueryResponse(BaseModel):
    prompt: str = Field(
        ..., description="The original user query prompt"
    )
    answer: str = Field(
        ..., description="The synthesized LLM response text generated based on the retrieved context"
    )
    retrieved_contexts: List[RetrievedDocument] = Field(
        default_factory=list, description="List of matched documents used as background context"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata dictionary tracking token counts, execution metrics, and fallback status"
    )
