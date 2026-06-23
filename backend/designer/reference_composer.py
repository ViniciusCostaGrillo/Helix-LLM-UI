from typing import List
from backend.database.chroma_client import ChromaClientManager
from backend.rag.embeddings import EmbeddingGenerator
from backend.utils.custom_logger import setup_logger

logger = setup_logger("designer.reference_composer")


class ReferenceComposer:
    """Composer that queries vector collections for masterpiece and design references matching the prompt."""

    def __init__(self) -> None:
        self.chroma = ChromaClientManager()
        self.generator = EmbeddingGenerator()

    def compose_references(self, prompt: str, limit: int = 3) -> List[str]:
        logger.info(f"ReferenceComposer: composing design references for prompt: '{prompt}'...")

        references = []

        # 1. Compute prompt embedding vector
        try:
            query_vector = self.generator.get_embedding(prompt)
        except Exception as e:
            logger.warning(f"Failed to generate embedding vector in ReferenceComposer: {e}. Using fallback references.")
            return self._get_fallback_references(prompt)

        # Collections list to query
        priority_collections = [
            "Masterpieces",
            "MasterpieceComponents",
            "MasterpieceAssets",
            "MasterpieceAnimations",
            "MasterpieceDesignSystems",
            "Components",
            "DesignSystems",
            "Skills",
            "Assets",
            "PromptTemplates"
        ]

        # 2. Query each collection and parse names
        for col in priority_collections:
            try:
                # Query ChromaDB collection
                res = self.chroma.query_similarity(
                    collection_name=col,
                    query_vector=query_vector,
                    limit=limit
                )
                for item in res.results:
                    # Look for site_id, name, or metadata tags
                    ref_name = item.metadata.get("site_id") or item.metadata.get("name") or item.id
                    if ref_name and ref_name not in references:
                        references.append(str(ref_name))
            except Exception as e:
                # Silently catch and skip (collections may not be populated or active)
                logger.debug(f"ReferenceComposer: collection '{col}' not queried or empty: {e}")

        # 3. Apply standard fallbacks to ensure rich reference lists
        fallback_refs = self._get_fallback_references(prompt)
        for ref in fallback_refs:
            if ref not in references:
                references.append(ref)

        logger.info(f"ReferenceComposer: compiled consolidated references list: {references}")
        return references[:5]  # limit to top 5 references

    def _get_fallback_references(self, prompt: str) -> List[str]:
        p_lower = prompt.lower()
        defaults = []

        if "luxury" in p_lower or "fashion" in p_lower:
            defaults = ["elara", "noirframe"]
        elif "saas" in p_lower or "tech" in p_lower or "linear" in p_lower:
            defaults = ["linear", "stripe", "vercel"]
        elif "refokus" in p_lower:
            defaults = ["refokus", "obys"]
        else:
            defaults = ["elara", "noirframe", "refokus", "linear", "stripe"]

        return defaults
