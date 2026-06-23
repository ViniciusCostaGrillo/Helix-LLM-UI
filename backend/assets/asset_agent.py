import logging
from typing import Any, Dict

from backend.assets.asset_library import AssetLibrary

logger = logging.getLogger(__name__)


class AssetAgent:
    """Agent that resolves and injects visual premium assets into the generated components."""

    def __init__(self) -> None:
        self.library = AssetLibrary()

    def resolve_assets_for_style(self, style_class: str) -> Dict[str, Any]:
        logger.info(f"AssetAgent: resolving asset bindings for style_class={style_class}...")

        resolved = {}
        if "luxury" in style_class:
            resolved["gradient"] = self.library.get_assets_by_type("gradients")[0]
            resolved["3d"] = self.library.get_assets_by_type("3d")[0]
        elif "saas" in style_class:
            resolved["gradient"] = self.library.get_assets_by_type("gradients")[1]
            resolved["icon"] = self.library.get_assets_by_type("icons")[1]
        else:
            resolved["gradient"] = self.library.get_assets_by_type("gradients")[2]

        return {
            "style_class": style_class,
            "resolved_assets": resolved,
            "status": "resolved",
        }
