from typing import List
from pydantic import BaseModel, Field


class VisualIntent(BaseModel):
    """Core visual targets extracted from user input/prompt."""
    industry: str = Field(..., description="Target industry (e.g. fashion, tech, real estate)")
    category: str = Field(..., description="Project category (e.g. ecommerce, landing page, dashboard)")
    style: List[str] = Field(default_factory=list, description="Styles to target (e.g. luxury, editorial, minimal)")
    theme: List[str] = Field(default_factory=list, description="Color modes (e.g. dark, light, custom)")
    animations: List[str] = Field(default_factory=list, description="Animation profiles (e.g. subtle, high, none)")
    priority: List[str] = Field(default_factory=list, description="Core visual elements to prioritize (e.g. typography, layout)")


class CreativeDirection(BaseModel):
    """Artistic parameters defined by the Creative Director Agent."""
    direction_statement: str = Field(..., description="Statement summarizing creative concept")
    typography: List[str] = Field(default_factory=list, description="Google Fonts or design font systems to use")
    colors: List[str] = Field(default_factory=list, description="Hex codes representing the color palette")
    animations: List[str] = Field(default_factory=list, description="GSAP/Lottie animation choices")
    assets: List[str] = Field(default_factory=list, description="Required assets (icons, particles, videos)")
    visual_hierarchy: List[str] = Field(default_factory=list, description="Guidelines for visual elements dominance")


class Moodboard(BaseModel):
    """Represents a curated design collection matching a design style."""
    style: str = Field(..., description="Name of the design style")
    colors: List[str] = Field(default_factory=list, description="Color palette colors")
    typography: List[str] = Field(default_factory=list, description="Fonts used in the style")
    references: List[str] = Field(default_factory=list, description="Premium websites referenced")


class VisualPlan(BaseModel):
    """Full architectural design layout and planning parameters compiled prior to React generation."""
    layout: List[str] = Field(default_factory=list, description="Order of layout blocks/components (e.g. ['hero', 'features', 'footer'])")
    theme: str = Field(..., description="Composite theme title (e.g. luxury-editorial-minimal)")
    spacing: str = Field(..., description="Overall spacing layout rule (e.g. spacious, compact, dynamic)")
    animations: str = Field(..., description="Primary animation manager (e.g. gsap, simple)")
    scroll: str = Field(..., description="Scroll behavior profile (e.g. lenis, normal)")
    background: str = Field(..., description="Canvas background layout/fill type (e.g. gradient, mesh, solid)")
    references: List[str] = Field(default_factory=list, description="Consolidated masterpieces and references")
    visual_intent: VisualIntent = Field(..., description="The original visual intent parameters")
    creative_direction: CreativeDirection = Field(..., description="The parsed creative director requirements")
    moodboard: Moodboard = Field(..., description="The loaded or generated moodboard data")
