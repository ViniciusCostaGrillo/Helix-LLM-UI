import hashlib
import json
import logging
import os
import shutil
from typing import Any, Dict
import yaml

from backend.database.chroma_client import ChromaClientManager

logger = logging.getLogger(__name__)


class KnowledgeBuilderAgent:
    """Agent that analyzes raw assets, components, design system specs, and skills,

    compiles them into their respective libraries, and indexes them in ChromaDB.
    """

    def __init__(self) -> None:
        self.chroma = ChromaClientManager()
        self.base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

    def generate_hash(self, file_path: str) -> str:
        """Generates MD5 hash of a file to check for updates."""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def ingest_file(self, file_path: str) -> Dict[str, Any]:
        """Ingests a file from the monitored directories and indexes it."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_hash = self.generate_hash(file_path)
        file_name = os.path.basename(file_path)
        relative_path = os.path.relpath(file_path, self.base_dir)

        # Detect category based on parent folder name
        parent_dir = os.path.basename(os.path.dirname(file_path))
        logger.info(
            f"Ingesting file: {relative_path} (detected category: {parent_dir})"
        )

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        metadata: Dict[str, Any] = {
            "file_name": file_name,
            "relative_path": relative_path,
            "hash": file_hash,
            "category": parent_dir,
            "size": os.path.getsize(file_path),
        }

        # Vector representation fallback (e.g. 128-dimensional mock vector)
        mock_vector = [0.1] * 128
        # Make it slightly unique based on name to simulate varied embeddings
        char_sum = sum(ord(c) for c in file_name) % 100
        mock_vector[0] = float(char_sum) / 100.0

        collection_name = "references"
        compiled_path = None

        if parent_dir == "components":
            collection_name = "Components"
            compiled_path = self._compile_component(file_name, content, metadata)
        elif parent_dir == "design_systems":
            collection_name = "DesignSystems"
            compiled_path = self._compile_design_system(file_name, content, metadata)
        elif parent_dir == "skills":
            collection_name = "Skills"
            compiled_path = self._compile_skill(file_name, content, metadata)
        elif parent_dir in ["assets", "images", "videos", "3d"]:
            collection_name = "Assets"
            compiled_path = self._copy_asset(parent_dir, file_name, file_path, metadata)
        elif parent_dir == "prompt_templates":
            collection_name = "PromptTemplates"
            metadata["template_type"] = "system_prompt"

        # Index in ChromaDB
        self.chroma.upsert(
            collection_name=collection_name,
            doc_id=relative_path.replace("\\", "/"),
            vector=mock_vector,
            document=content[:10000],  # store segment of content
            metadata=metadata,
        )

        return {
            "status": "success",
            "file_path": relative_path,
            "hash": file_hash,
            "collection": collection_name,
            "compiled_to": compiled_path,
        }

    def _compile_component(
        self, file_name: str, content: str, metadata: Dict[str, Any]
    ) -> str:
        """Processes a TSX/JSX component and compiles it to the component library."""
        # Determine component subfolder
        name_lower = file_name.lower()
        subfolder = "cards"
        if "hero" in name_lower:
            subfolder = "hero"
        elif "nav" in name_lower or "header" in name_lower:
            subfolder = "navbar"
        elif "price" in name_lower or "pricing" in name_lower:
            subfolder = "pricing"
        elif "footer" in name_lower:
            subfolder = "footer"

        target_dir = os.path.join(self.base_dir, "component_library", subfolder)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, file_name)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

        metadata["component_type"] = subfolder
        logger.info(
            f"Compiled component: {file_name} -> component_library/{subfolder}/"
        )
        return os.path.relpath(target_path, self.base_dir)

    def _compile_design_system(
        self, file_name: str, content: str, metadata: Dict[str, Any]
    ) -> str:
        """Processes a design system specification and compiles it to the design system library."""
        # Determine subfolder style
        name_lower = file_name.lower()
        subfolder = "saas"
        for style in [
            "luxury",
            "saas",
            "portfolio",
            "dashboard",
            "startup",
            "agency",
            "minimal",
            "glassmorphism",
        ]:
            if style in name_lower:
                subfolder = style
                break

        target_dir = os.path.join(self.base_dir, "design_systems", subfolder)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, file_name)

        # Parse and enrich content metadata if YAML/JSON
        try:
            if file_name.endswith(".yaml") or file_name.endswith(".yml"):
                parsed = yaml.safe_load(content)
                metadata["design_rules_count"] = (
                    len(parsed.get("rules", [])) if isinstance(parsed, dict) else 0
                )
            elif file_name.endswith(".json"):
                parsed = json.loads(content)
                metadata["design_rules_count"] = (
                    len(parsed.get("rules", [])) if isinstance(parsed, dict) else 0
                )
        except Exception:
            pass

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(
            f"Compiled design system: {file_name} -> design_systems/{subfolder}/"
        )
        return os.path.relpath(target_path, self.base_dir)

    def _compile_skill(
        self, file_name: str, content: str, metadata: Dict[str, Any]
    ) -> str:
        """Processes a skill configuration and registers/updates system skills."""
        # Write skill config to target skill folders if necessary
        target_dir = os.path.join(self.base_dir, "backend", "skills")
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, file_name)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Compiled skill definition: {file_name} -> backend/skills/")
        return os.path.relpath(target_path, self.base_dir)

    def _copy_asset(
        self, parent_dir: str, file_name: str, file_path: str, metadata: Dict[str, Any]
    ) -> str:
        """Copies assets to the static directory or respective folders."""
        target_dir = os.path.join(self.base_dir, "backend", "assets", parent_dir)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, file_name)

        shutil.copy2(file_path, target_path)
        logger.info(f"Copied asset: {file_name} -> backend/assets/{parent_dir}/")
        return os.path.relpath(target_path, self.base_dir)
