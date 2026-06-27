from typing import List
from backend.schemas.analyzer import AnalysisResult, ComponentMetadata
from backend.schemas.codegen import GeneratedComponent
from backend.schemas.embeddings import ComponentEmbedding, PageEmbedding, StyleEmbedding
from backend.schemas.extractor import ExtractionResult
from backend.schemas.vision import VisionMetadata
from backend.utils.custom_logger import setup_logger

logger = setup_logger("rag.embeddings")

# Global cached model singleton
_cached_transformer_model = None


class EmbeddingGenerator:
    """Service to generate dense float vector embeddings (384 dimensions)

    for pages, components, and design styles using pre-trained SentenceTransformer models offline.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        logger.debug(f"EmbeddingGenerator initialized using model: {self.model_name}")

    @property
    def model(self):
        global _cached_transformer_model
        if _cached_transformer_model is None:
            logger.info(f"Loading SentenceTransformer model '{self.model_name}' offline...")
            from sentence_transformers import SentenceTransformer
            _cached_transformer_model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully.")
        return _cached_transformer_model

    def get_embedding(self, text: str) -> List[float]:
        """Encodes a single text string into a dense float vector."""
        if not text or not text.strip():
            logger.warning("Empty text received for embedding. Generating zeros.")
            # MiniLM-L6-v2 has 384 dimensions
            return [0.0] * 384

        try:
            vector = self.model.encode(text, convert_to_numpy=True)
            return vector.tolist()
        except Exception as e:
            logger.exception(f"Failed to generate embedding for text: {e}")
            raise

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Encodes a list of text strings in batch mode."""
        if not texts:
            return []

        try:
            vectors = self.model.encode(texts, convert_to_numpy=True)
            return vectors.tolist()
        except Exception as e:
            logger.exception(f"Failed to generate batch embeddings: {e}")
            raise

    def generate_page_embedding(
        self, extraction: ExtractionResult, analysis: AnalysisResult
    ) -> PageEmbedding:
        """Assembles a semantic page details paragraph and embeds it."""
        title = extraction.metadata.title or "Untitled Page"
        clean_text = extraction.clean_text or ""
        purpose = analysis.page_purpose or "web_page"

        text_source = (
            f"Page Title: {title}\n"
            f"Purpose: {purpose}\n"
            f"Body Content:\n{clean_text}"
        )

        logger.debug(f"Generating page embedding for: {title}")
        vector = self.get_embedding(text_source)
        return PageEmbedding(page_vector=vector, text_source=text_source)

    def generate_component_embedding(
        self, component: GeneratedComponent, comp_meta: ComponentMetadata
    ) -> ComponentEmbedding:
        """Assembles a component descriptor containing typescript code details and embeds it."""
        comp_id = comp_meta.component_id
        name = component.name
        comp_type = comp_meta.type
        desc = comp_meta.description
        classes = " ".join(comp_meta.style_classes)
        code = component.code

        text_source = (
            f"Component Name: {name}\n"
            f"Type: {comp_type}\n"
            f"Description: {desc}\n"
            f"Style classes: {classes}\n"
            f"Source Code:\n{code}"
        )

        logger.debug(f"Generating component embedding for: {name} ({comp_id})")
        vector = self.get_embedding(text_source)
        return ComponentEmbedding(
            component_id=comp_id, vector=vector, text_source=text_source
        )

    def generate_style_embedding(
        self, analysis: AnalysisResult, vision: VisionMetadata
    ) -> StyleEmbedding:
        """Assembles design theme details, margins, grids, and colors, and embeds it."""
        theme = analysis.theme
        layout = analysis.layout
        density = vision.density
        grid = vision.grid

        text_source = (
            f"Design Palette:\n"
            f"- Primary color: {theme.primary_color}\n"
            f"- Secondary color: {theme.secondary_color}\n"
            f"- Background color: {theme.background_color}\n"
            f"- Typography: {', '.join(theme.fonts)}\n"
            f"Spacing Profile:\n"
            f"- Margins: {vision.spacing.margins}\n"
            f"- Content area density: {density.content_percentage}%\n"
            f"Grid Configuration: {grid.grid_type}\n"
            f"Layout breakdown: {layout.grid_structure}"
        )

        logger.debug("Generating design tokens style embedding")
        vector = self.get_embedding(text_source)
        return StyleEmbedding(vector=vector, text_source=text_source)
