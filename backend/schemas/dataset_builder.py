from typing import Dict
from pydantic import BaseModel, Field


class DatasetManifest(BaseModel):
    site_id: str = Field(
        ..., description="Padded site identifier (e.g., site_000001)"
    )
    url: str = Field(
        ..., description="Original URL the page was crawled from"
    )
    created_at: str = Field(
        ..., description="UTC ISO timestamp of the dataset generation"
    )
    components_count: int = Field(
        0, description="Total count of generated React components"
    )
    primary_color: str = Field(
        ..., description="Main primary hex color token identified"
    )
    background_color: str = Field(
        ..., description="Main background hex color token identified"
    )
    content_density: float = Field(
        ..., description="Calculated percentage of active layout space (0.0 to 100.0)"
    )
    files_mapping: Dict[str, str] = Field(
        default_factory=dict, description="Relative paths mapping of all assets in the package"
    )
