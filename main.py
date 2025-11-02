"""
Development server for BotCanvas API
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure backend package is registered for relative imports when running as script
if __package__ is None:  # Direct execution (e.g., uvicorn main:app)
    import os
    import sys

    sys.path.append(os.path.dirname(__file__))

from api.v1.nodes import router as nodes_router
from api.v1.credentials import router as credentials_router
from api.v1.workflows import router as workflows_router
from api.v1.vector_store import router as vector_store_router
from api.v1.deployments import router as deployments_router
from api.v1.templates import router as templates_router

# Load environment variables
load_dotenv()

# Register all nodes on startup
try:
    from register_nodes import register_all_nodes
    register_all_nodes()
except ImportError as e:
    print(f"Warning: Could not register nodes: {e}")

# Create performance indexes on startup
try:
    from db_migrations import create_performance_indexes
    create_performance_indexes()
except Exception as e:
    print(f"Warning: Could not create indexes: {e}")

# Create FastAPI app for development
app = FastAPI(
    title="BotCanvas API - Development",
    description="Development server for no-code chatbot builder API",
    version="dev",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for development (allow all origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development: allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(nodes_router, prefix="/api/v1")
app.include_router(credentials_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")
app.include_router(vector_store_router)
app.include_router(deployments_router, prefix="/api/v1")
app.include_router(templates_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BotCanvas API - Development Server",
        "version": "dev",
        "docs": "/docs",
        "endpoints": {
            "nodes": "/api/v1/nodes",
            "credentials": "/api/v1/credentials",
            "workflows": "/api/v1/workflows",
            "vector-store": "/api/v1/vector-store",
            "deployments": "/api/v1/deployments",
            "templates": "/api/v1/templates"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "BotCanvas API - Development"}

if __name__ == "__main__":
    print("[START] Starting BotCanvas Development Server...")
    print("[DOCS] API Documentation: http://localhost:8000/docs")
    print("[WEB] API Base URL: http://localhost:8000")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
