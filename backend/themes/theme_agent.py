import logging
from typing import Any, Dict
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ThemeConfig(BaseModel):
    name: str
    bg_color: str
    text_color: str
    accent_color: str
    border_color: str
    font_family: str
    extra_styles: Dict[str, Any] = Field(default_factory=dict)


class ThemeAgent:
    """Agent that resolves dynamic themes (dark, light, luxury, glass, minimal) and styling parameters."""

    def __init__(self) -> None:
        self.themes: Dict[str, ThemeConfig] = {
            "dark": ThemeConfig(
                name="Dark Theme",
                bg_color="#0f172a",
                text_color="#f8fafc",
                accent_color="#3b82f6",
                border_color="#334155",
                font_family="'Inter', sans-serif",
                extra_styles={"shadow": "shadow-lg shadow-black/50"},
            ),
            "light": ThemeConfig(
                name="Light Theme",
                bg_color="#ffffff",
                text_color="#0f172a",
                accent_color="#2563eb",
                border_color="#e2e8f0",
                font_family="'Inter', sans-serif",
                extra_styles={"shadow": "shadow-md shadow-slate-100"},
            ),
            "luxury": ThemeConfig(
                name="Luxury Gold Theme",
                bg_color="#090500",
                text_color="#f5e0c3",
                accent_color="#d4af37",
                border_color="#3a2e1e",
                font_family="'Playfair Display', serif",
                extra_styles={
                    "shadow": "shadow-2xl shadow-yellow-950/20",
                    "backdrop_blur": "blur(4px)",
                    "letter_spacing": "tracking-wide",
                },
            ),
            "glass": ThemeConfig(
                name="Glassmorphism Theme",
                bg_color="rgba(255, 255, 255, 0.08)",
                text_color="#ffffff",
                accent_color="#a855f7",
                border_color="rgba(255, 255, 255, 0.15)",
                font_family="'Outfit', sans-serif",
                extra_styles={
                    "backdrop_filter": "blur(12px) saturate(180%)",
                    "shadow": "shadow-[0_8px_32px_0_rgba(31,38,135,0.07)]",
                },
            ),
            "minimal": ThemeConfig(
                name="Minimalist Slate Theme",
                bg_color="#f8fafc",
                text_color="#1e293b",
                accent_color="#0f172a",
                border_color="#cbd5e1",
                font_family="'Roboto Mono', monospace",
                extra_styles={
                    "border_width": "border-2",
                    "shadow": "none",
                    "uppercase": "uppercase",
                },
            ),
        }

    def resolve_theme(self, theme_name: str) -> Dict[str, Any]:
        logger.info(
            f"ThemeAgent: resolving style configurations for theme={theme_name}..."
        )
        theme = self.themes.get(theme_name.lower())
        if not theme:
            logger.warning(
                f"ThemeAgent: theme '{theme_name}' not found. Falling back to 'dark'."
            )
            theme = self.themes["dark"]
        return theme.model_dump()
