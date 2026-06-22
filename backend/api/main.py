from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.api.routers import all_routers
from backend.utils.custom_logger import setup_logger

# Setup structured logger
logger = setup_logger("api.main")

# Initialize FastAPI application
app = FastAPI(
    title="UI AI Ecosystem API",
    description="Backend API for crawling, pattern analysis, and RAG React-Tailwind code generation.",
    version="1.0.0"
)

# Configure CORS for local Next.js client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom API Exception class
class APIException(Exception):
    def __init__(self, status_code: int, message: str, details: any = None):
        self.status_code = status_code
        self.message = message
        self.details = details

# Register custom exception handlers
@app.exception_handler(APIException)
def api_exception_handler(request: Request, exc: APIException):
    logger.error(f"API Error handling request {request.url.path}: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details or {}
        }
    )

@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An unexpected server error occurred."}
    )

# Register routers dynamically
for router in all_routers:
    app.include_router(router)

@app.get("/health", tags=["system"])
def health_check():
    logger.debug("Health check requested")
    return {"status": "healthy", "service": "api"}
