import os
import shutil
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, UploadFile, File, status

logger = logging.getLogger("api.routers.knowledge")

router = APIRouter(prefix="/knowledge", tags=["Knowledge Ingestion"])

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
INPUT_ROOT = os.path.join(BASE_DIR, "knowledge_input")


def classify_file(filename: str) -> str:
    """Classifies file types into their correct target folders within knowledge_input."""
    name_lower = filename.lower()
    _, ext = os.path.splitext(name_lower)

    if ext in [".tsx", ".jsx", ".ts", ".js"]:
        return "components"
    elif ext in [".glb", ".gltf"]:
        return "3d"
    elif ext in [".png", ".jpg", ".jpeg", ".svg"]:
        return "images"
    elif ext in [".mp4", ".webm", ".avi"]:
        return "videos"
    elif ext in [".yaml", ".yml", ".json"]:
        if "skill" in name_lower:
            return "skills"
        elif "design" in name_lower or "theme" in name_lower:
            return "design_systems"
        elif "prompt" in name_lower or "template" in name_lower:
            return "prompt_templates"
        # If it's a generic config yaml/json, default to design_systems if it doesn't match others
        return "design_systems"
    elif ext == ".txt":
        return "references"

    return "references"


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_knowledge_files(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    """Receives files, automatically classifies them based on extension and filename,

    saves them to the corresponding monitored folders in knowledge_input/, and returns results.
    """
    logger.info(
        f"Received request to upload {len(files)} files for knowledge ingestion..."
    )
    results = []

    for file in files:
        if not file.filename:
            continue

        category = classify_file(file.filename)
        target_dir = os.path.join(INPUT_ROOT, category)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, file.filename)

        try:
            with open(target_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            rel_path = os.path.relpath(target_path, BASE_DIR).replace("\\", "/")
            logger.info(
                f"File '{file.filename}' classified as '{category}' and saved to '{rel_path}'"
            )

            results.append(
                {
                    "filename": file.filename,
                    "category": category,
                    "target_path": rel_path,
                    "status": "success",
                }
            )
        except Exception as e:
            logger.error(f"Failed to save uploaded file '{file.filename}': {e}")
            results.append(
                {
                    "filename": file.filename,
                    "category": category,
                    "status": "failed",
                    "error": str(e),
                }
            )

    return {"uploaded_files": results, "count": len(results)}


@router.get("/files", status_code=status.HTTP_200_OK)
async def list_knowledge_files() -> Dict[str, List[Dict[str, Any]]]:
    """Lists all files stored in the monitored knowledge_input folders."""
    logger.info("Listing files in monitored knowledge_input directories...")
    grouped_files: Dict[str, List[Dict[str, Any]]] = {
        "components": [],
        "design_systems": [],
        "skills": [],
        "prompt_templates": [],
        "images": [],
        "videos": [],
        "3d": [],
        "references": [],
    }

    if not os.path.exists(INPUT_ROOT):
        return grouped_files

    for category in grouped_files.keys():
        dir_path = os.path.join(INPUT_ROOT, category)
        if os.path.exists(dir_path):
            for file_name in os.listdir(dir_path):
                if file_name.startswith(".") or file_name == ".gitkeep":
                    continue
                file_path = os.path.join(dir_path, file_name)
                stats = os.stat(file_path)
                grouped_files[category].append(
                    {
                        "name": file_name,
                        "size": stats.st_size,
                        "modified": stats.st_mtime,
                        "relative_path": os.path.relpath(file_path, BASE_DIR).replace(
                            "\\", "/"
                        ),
                    }
                )

    return grouped_files
