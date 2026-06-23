import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class AssetLibrary:
    """Contains standard presets catalog of backgrounds, gradients, textures, 3D files, icons, and videos."""

    def __init__(self) -> None:
        self.gradients = [
            {"id": "luxury_gold", "css": "linear-gradient(135deg, #f59e0b 0%, #78350f 100%)"},
            {"id": "saas_indigo", "css": "linear-gradient(135deg, #6366f1 0%, #4338ca 100%)"},
            {
                "id": "glass_mesh",
                "css": "radial-gradient(at 0% 0%, #3b82f6 0, transparent 50%), radial-gradient(at 50% 0%, #10b981 0, transparent 50%)",
            },
        ]
        self.textures = [
            {"id": "noise", "path": "/assets/textures/noise.png"},
            {"id": "grid_paper", "path": "/assets/textures/grid.svg"},
        ]
        self.icons = [
            {"id": "arrow_right", "svg": "<svg>...</svg>"},
            {"id": "dashboard", "svg": "<svg>...</svg>"},
        ]
        self.three_d = [
            {"id": "shoes_glb", "path": "/assets/3d/shoes.glb"},
            {"id": "abstract_sphere", "path": "/assets/3d/sphere.glb"},
        ]
        self.videos = [
            {"id": "ambient_loop", "path": "/assets/videos/ambient.mp4"},
        ]

    def get_assets_by_type(self, asset_type: str) -> List[Dict[str, Any]]:
        if asset_type == "gradients":
            return self.gradients
        elif asset_type == "textures":
            return self.textures
        elif asset_type == "icons":
            return self.icons
        elif asset_type == "3d":
            return self.three_d
        elif asset_type == "videos":
            return self.videos
        return []
