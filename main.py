"""
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.nodes import router as nodes_router

# Register all nodes on startup
try:
    from register_nodes import register_all_nodes
    register_all_nodes()
except ImportError as e:
    print(f"Warning: Could not register nodes: {e}")

# Create FastAPI app
app = FastAPI(
    title="BotCanvas API",
    description="No-code chatbot builder API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(nodes_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "BotCanvas API",
        "version": "1.0.0",
        "description": "No-code chatbot builder API",
        "docs": "/docs",
        "endpoints": {
            "nodes": "/api/v1/nodes"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "BotCanvas API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
