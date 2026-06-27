import logging
from typing import List, Dict, Any
from backend.database.chroma_client import ChromaClientManager

logger = logging.getLogger(__name__)


class MasterpieceEmbeddingsManager:
    """Handles generating embeddings and indexing masterpiece documents in ChromaDB collections."""

    def __init__(self) -> None:
        self.chroma = ChromaClientManager()
        self._encoder = None
        
    @property
    def encoder(self):
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("SentenceTransformer loaded successfully for Masterpieces embeddings.")
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer: {e}. Falling back to mock embeddings.")
        return self._encoder

    def get_vector(self, text: str) -> List[float]:
        """Generates a 128-dimensional embedding vector (padded/mocked if no encoder)."""
        encoder = self.encoder
        if encoder:
            try:
                emb = encoder.encode(text).tolist()
                # If MiniLM-L6-v2, size is 384. pad/slice to 128 or use as-is.
                # Actually, standardizing to the size of the encoder is best, but let's pad/slice to 128
                # to keep it aligned with other database collections which use 128.
                if len(emb) > 128:
                    return emb[:128]
                elif len(emb) < 128:
                    return emb + [0.0] * (128 - len(emb))
                return emb
            except Exception as e:
                logger.error(f"Error generating embedding via SentenceTransformer: {e}")

        # Fallback Mock Vector
        mock = [0.15] * 128
        char_sum = sum(ord(c) for c in text[:50]) % 100
        mock[0] = float(char_sum) / 100.0
        return mock

    def index_masterpiece_item(
        self,
        collection_name: str,
        item_id: str,
        document: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Indexes a specific masterpiece asset, component, or design system in ChromaDB."""
        # Ensure it has masterpiece=true and high weight
        metadata["masterpiece"] = True
        metadata["weight"] = metadata.get("weight", 10)
        
        vector = self.get_vector(document)
        logger.info(f"Indexing masterpiece item '{item_id}' in ChromaDB collection '{collection_name}' with weight {metadata['weight']}.")
        
        self.chroma.upsert(
            collection_name=collection_name,
            doc_id=item_id,
            vector=vector,
            document=document[:10000],
            metadata=metadata
        )
