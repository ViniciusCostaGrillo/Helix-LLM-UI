from typing import List, Dict, Any
from backend.utils.custom_logger import setup_logger

logger = setup_logger("designer.style_composer")


class StyleComposer:
    """Composer that merges multiple design styles into unified composite visual identities."""

    def compose_style_tag(self, styles: List[str]) -> str:
        if not styles:
            return "minimal"
        
        # Deduplicate while preserving order, clean and format
        seen = set()
        cleaned_styles = []
        for s in styles:
            s_clean = s.lower().strip().replace(" ", "-")
            if s_clean not in seen and s_clean:
                seen.add(s_clean)
                cleaned_styles.append(s_clean)

        # Truncate to maximum 4 terms to keep tags manageable
        composite_tag = "-".join(cleaned_styles[:4])
        logger.info(f"StyleComposer: composed style tag '{composite_tag}' from inputs: {styles}")
        return composite_tag

    def resolve_style_properties(self, styles: List[str]) -> Dict[str, Any]:
        """Resolves consolidated fonts and colors properties based on a list of active styles."""
        logger.info(f"StyleComposer: merging visual properties for styles: {styles}")
        
        # Default fallback tokens
        resolved_colors = ["#111827", "#3b82f6", "#10b981", "#f9fafb"]
        resolved_fonts = ["Inter"]

        style_slugs = [s.lower().strip() for s in styles]

        # Prioritized resolution
        if "luxury" in style_slugs:
            resolved_colors = ["#0b0a0f", "#d4af37", "#f5f5f7", "#1a1824"]
            resolved_fonts = ["Playfair Display", "Inter"]
            if "editorial" in style_slugs:
                resolved_fonts = ["Playfair Display", "Lora", "Inter"]
        elif "editorial" in style_slugs:
            resolved_colors = ["#fcfbf9", "#111111", "#444444", "#a39081"]
            resolved_fonts = ["Lora", "Inter"]
        elif "saas" in style_slugs or "tech" in style_slugs:
            resolved_colors = ["#000000", "#0072f5", "#f4f4f5", "#8f8f93"]
            resolved_fonts = ["Inter", "Geist"]
            if "glassmorphism" in style_slugs:
                resolved_colors = ["#0f172a", "#38bdf8", "#f8fafc", "#64748b"]
        elif "minimal" in style_slugs:
            resolved_colors = ["#fafafa", "#171717", "#e5e5e5", "#737373"]
            resolved_fonts = ["Helvetica Neue", "Inter"]

        return {
            "colors": resolved_colors,
            "fonts": resolved_fonts
        }
