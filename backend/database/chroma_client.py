import os
from typing import Any, Dict, List
import chromadb
from chromadb.config import Settings
from backend.schemas.chromadb import ChromaQueryResponse, ChromaResultItem
from backend.utils.custom_logger import setup_logger

logger = setup_logger("database.chroma_client")

# Global singleton connection cache
_cached_chroma_client = None


class ChromaClientManager:
    """Manager for ChromaDB connection, collection initialization,

    record updates (upserts), and vector searches.
    """

    def __init__(self) -> None:
        global _cached_chroma_client
        if _cached_chroma_client is not None:
            self.client = _cached_chroma_client
            return

        host = os.getenv("CHROMADB_HOST", "localhost")
        port = int(os.getenv("CHROMADB_PORT", "8000"))
        
        # Try connecting to the HTTP client (standard for Docker setup)
        try:
            logger.info(f"Attempting connection to ChromaDB server at http://{host}:{port}...")
            self.client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(allow_reset=True)
            )
            # Test connection by listing collections
            self.client.list_collections()
            logger.info("Connected to ChromaDB server successfully.")
            _cached_chroma_client = self.client
        except Exception as e:
            logger.warning(
                f"Failed to connect to ChromaDB server: {e}. "
                "Falling back to local persistent on-disk storage..."
            )
            # Fall back to local persistent client
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, "storage", "chromadb")
            os.makedirs(db_path, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=db_path,
                settings=Settings(allow_reset=True)
            )
            logger.info(f"Initialized local ChromaDB PersistentClient at: {db_path}")
            _cached_chroma_client = self.client

    def get_or_create_collection(self, collection_name: str) -> Any:
        """Retrieves or initializes a vector collection by name."""
        logger.debug(f"Getting or creating ChromaDB collection: {collection_name}")
        return self.client.get_or_create_collection(name=collection_name)

    def upsert(
        self,
        collection_name: str,
        doc_id: str,
        vector: List[float],
        document: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Inserts or updates a document with its float vector representation and metadata."""
        logger.debug(f"Upserting document '{doc_id}' into collection '{collection_name}'...")
        collection = self.get_or_create_collection(collection_name)
        collection.upsert(
            ids=[doc_id],
            embeddings=[vector],
            documents=[document],
            metadatas=[metadata],
        )
        logger.debug("Upsert complete.")

    def query_similarity(
        self, collection_name: str, query_vector: List[float], limit: int = 5
    ) -> ChromaQueryResponse:
        """Finds similarity matches in the collection using query vectors."""
        logger.info(
            f"Executing semantic similarity query in collection '{collection_name}' (limit={limit})..."
        )
        collection = self.get_or_create_collection(collection_name)
        
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )

        items = []
        if results and "ids" in results and results["ids"]:
            # Results are nested list coordinates (since multiple queries can be passed)
            ids = results["ids"][0]
            distances = results.get("distances", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            documents = results.get("documents", [[]])[0]

            for idx in range(len(ids)):
                items.append(
                    ChromaResultItem(
                        id=ids[idx],
                        distance=distances[idx] if idx < len(distances) else 0.0,
                        metadata=metadatas[idx] if idx < len(metadatas) else {},
                        document=documents[idx] if (documents and idx < len(documents)) else None,
                    )
                )

        logger.info(f"Similarity query completed. Mapped {len(items)} results.")
        return ChromaQueryResponse(results=items)

    def reset(self) -> None:
        """Resets the vector database collections (useful for testing cleanups)."""
        logger.info("Resetting ChromaDB database...")
        self.client.reset()
        logger.info("ChromaDB reset complete.")
