from backend.api.routers.generation import router as generation_router
from backend.api.routers.crawler import router as crawler_router
from backend.api.routers.analyzer import router as analyzer_router
from backend.api.routers.dataset import router as dataset_router
from backend.api.routers.projects import router as projects_router
from backend.api.routers.components import router as components_router
from backend.api.routers.styles import router as styles_router

# List of all configured routers
all_routers = [
    generation_router,
    crawler_router,
    analyzer_router,
    dataset_router,
    projects_router,
    components_router,
    styles_router
]
