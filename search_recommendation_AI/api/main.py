# ============================================================================
# FILE: api/main.py
# ============================================================================


import logging

print("DEBUG: Starting app import sequence")

try:
    from config import config
    print("DEBUG: Imported config ✅")
except Exception as e:
    print("DEBUG: Failed to import config ❌", e)
    raise

try:
    from routes import search, recommendations
    print("DEBUG: Imported routes ✅")
except Exception as e:
    print("DEBUG: Failed to import routes ❌", e)
    raise

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import config
from routes import search, recommendations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("=" * 80)
    logger.info("Starting Artwork Search & Recommendation API")
    logger.info("=" * 80)
    config.validate()
    logger.info("API is ready to accept requests")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API")
    from mongo_client import mongo_client
    mongo_client.close()
    logger.info("API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Artwork Search & Recommendation API",
    description="Semantic search and recommendations for artwork marketplace",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
# --- ✅ CORS CONFIGURATION ---
# Define allowed frontend origins
allowed_origins = [
    "http://localhost:3000",  # local React dev
    "https://art-marketplace-frontend-kboua6urdq-el.a.run.app",  # replace with your actual Vercel domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- END CORS CONFIGURATION ---


# --- THIS IS THE FIX ---
# Include routers with the correct prefix
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["Recommendations"])
# --- END OF FIX ---


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Artwork Search & Recommendation API",
        "version": "1.0.0"
    }


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Detailed health check endpoint."""
    health_status = {
        "status": "healthy",
        "components": {
            "mongodb": "unknown",
            "redis": "unknown",
            "vertex_ai": "unknown"
        }
    }
    
    # Check MongoDB
    try:
        from mongo_client import mongo_client
        mongo_client.client.server_info()
        health_status["components"]["mongodb"] = "healthy"
    except Exception as e:
        health_status["components"]["mongodb"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        from cache import cache
        if cache.client:
            cache.client.ping()
            health_status["components"]["redis"] = "healthy"
        else:
            health_status["components"]["redis"] = "disabled"
    except Exception as e:
        health_status["components"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Vertex AI
    try:
        from vertex_ai_client import vertex_ai_client
        if vertex_ai_client.endpoint:
            health_status["components"]["vertex_ai"] = "healthy"
        else:
            health_status["components"]["vertex_ai"] = "endpoint not configured"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["vertex_ai"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))    
    uvicorn.run(app, host="0.0.0.0", port=8080)
    