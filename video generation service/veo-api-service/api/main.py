# ============================================================================
# FILE: veo-api-service/api/main.py
# ============================================================================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import reels

# Initialize FastAPI app
app = FastAPI(
    title="Veo API Service",
    description="API service for serving AI-generated video reels",
    version="1.0.0"
)

# Configure CORS to allow frontend access
# Update these origins to match your frontend domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://cedar-defender-475318-r5.web.app",  # Firebase Hosting
        "https://cedar-defender-475318-r5.firebaseapp.com",  # Firebase Hosting alternate
        "https://art-marketplace-frontend-kboua6urdq-el.a.run.app",  # Cloud Run Frontend
        "http://localhost:5173",  # Local Vite dev server
        "http://localhost:3000",  # Alternative local dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reels.router, tags=["reels"])

# Health check endpoint
@app.get("/")
async def root():
    return {
        "service": "veo-api-service",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}