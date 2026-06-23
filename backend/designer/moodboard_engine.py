import os
import json
from pathlib import Path
from backend.schemas.designer import Moodboard
from backend.utils.custom_logger import setup_logger

logger = setup_logger("designer.moodboard_engine")


class MoodboardEngine:
    """Engine that manages loading, generating, and persisting visual moodboards."""

    def __init__(self) -> None:
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.moodboards_dir = self.base_dir / "knowledge" / "moodboards"
        os.makedirs(self.moodboards_dir, exist_ok=True)

    def load_or_create(self, style: str) -> Moodboard:
        style_slug = style.lower().strip().replace(" ", "_")
        file_path = self.moodboards_dir / f"{style_slug}.json"

        logger.info(f"MoodboardEngine: loading moodboard for style '{style_slug}'...")

        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"MoodboardEngine: successfully loaded preset file: {file_path}")
                return Moodboard.model_validate(data)
            except Exception as e:
                logger.warning(f"Failed to read moodboard file '{file_path}': {e}. Generating default.")

        # If not found or failed, generate a fallback moodboard
        moodboard = self._generate_fallback(style_slug)
        
        # Save it for future loads
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(moodboard.model_dump(), f, indent=2)
            logger.info(f"MoodboardEngine: persisted newly generated moodboard under: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write moodboard to file '{file_path}': {e}")

        return moodboard

    def _generate_fallback(self, style_slug: str) -> Moodboard:
        logger.info(f"MoodboardEngine: generating default moodboard for '{style_slug}'")
        
        colors = ["#121212", "#3b82f6", "#f3f4f6", "#4b5563"]
        typography = ["Inter", "Roboto"]
        references = ["linear", "stripe"]

        if "luxury" in style_slug:
            colors = ["#0b0a0f", "#d4af37", "#f5f5f7", "#1a1824"]
            typography = ["Playfair Display", "Inter"]
            references = ["elara", "noirframe"]
        elif "saas" in style_slug:
            colors = ["#000000", "#0072f5", "#f4f4f5", "#8f8f93"]
            typography = ["Inter", "Geist"]
            references = ["vercel", "linear"]
        elif "minimal" in style_slug:
            colors = ["#fafafa", "#171717", "#e5e5e5", "#737373"]
            typography = ["Helvetica Neue", "Inter"]
            references = ["minimalist-gallery", "linear"]
        elif "fashion" in style_slug:
            colors = ["#050505", "#ff3b30", "#ffffff", "#8e8e93"]
            typography = ["Bodoni Moda", "Montserrat"]
            references = ["noirframe"]
        elif "editorial" in style_slug:
            colors = ["#fcfbf9", "#111111", "#444444", "#a39081"]
            typography = ["Lora", "Inter"]
            references = ["elara"]

        return Moodboard(
            style=style_slug,
            colors=colors,
            typography=typography,
            references=references
        )
