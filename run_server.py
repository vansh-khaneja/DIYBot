"""
Run script for BotCanvas API
"""

import uvicorn
import sys
import os

if __name__ == "__main__":
    print("🚀 Starting BotCanvas API...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Alternative docs: http://localhost:8000/redoc")
    print("🌐 API Base URL: http://localhost:8000")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
