from typing import List, Optional
from pydantic import BaseModel, Field


class DesignTheme(BaseModel):
    primary_color: str = Field(
        ..., description="Hex code of the dominant primary/brand color"
    )
    secondary_color: str = Field(
        ..., description="Hex code of the accent or secondary design color"
    )
    background_color: str = Field(
        ..., description="Hex code of the body background canvas"
    )
    text_color: str = Field(
        ..., description="Hex code of the primary body text color"
    )
    fonts: List[str] = Field(
        default_factory=list, description="List of font family names used on the page"
    )


class ComponentMetadata(BaseModel):
    component_id: str = Field(
        ..., description="Unique alphanumeric identifier (e.g. comp_001, header_nav)"
    )
    type: str = Field(
        ..., description="Standard component type (e.g., button, card, header, hero, footer, list)"
    )
    description: str = Field(
        ..., description="Detailed description of what this component is and its visual placement"
    )
    layout_type: str = Field(
        ..., description="Identified layout system (e.g., flex-row, flex-col, grid, grid-cols-3)"
    )
    text_content: List[str] = Field(
        default_factory=list, description="Key text blocks and labels inside this component"
    )
    style_classes: List[str] = Field(
        default_factory=list, description="Associated styles or Tailwind classes used for the element"
    )


class LayoutAnalysis(BaseModel):
    grid_structure: str = Field(
        ..., description="Detailed breakdown of layout sections and visual alignment rules"
    )
    spacing_feel: str = Field(
        ..., description="Overall padding and spacing description (e.g., tight, compact, spacious, modern)"
    )
    responsiveness: str = Field(
        ..., description="Heuristic estimate of page responsiveness and responsive layout rules"
    )


class AnalysisResult(BaseModel):
    page_purpose: str = Field(
        ..., description="Identified website category (e.g., landing_page, portfolio, blog, dashboard)"
    )
    theme: DesignTheme = Field(
        ..., description="Extracted design tokens and color scheme palette"
    )
    components: List[ComponentMetadata] = Field(
        default_factory=list, description="List of UI components detected on the page layout"
    )
    layout: LayoutAnalysis = Field(
        ..., description="Detailed page design structure analysis"
    )
    ai_recommendations: Optional[str] = Field(
        None, description="Suggestions for improving layout or rendering in React + Tailwind CSS"
    )
