#!/usr/bin/env python3
"""Minimal Railway app - single file deployment."""

from fastapi import FastAPI, HTTPException
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SparkJar Memory Service",
    description="Minimal deployment for Railway",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "memory-service",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "port": os.getenv("PORT", "unknown")
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "memory-service",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": {
            "port": os.getenv("PORT", "unknown"),
            "database_url": "configured" if os.getenv("DATABASE_URL") else "not configured",
            "railway_environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown")
        }
    }

@app.on_event("startup")
async def startup():
    """Startup event."""
    logger.info("Memory Service starting up...")
    logger.info(f"PORT: {os.getenv('PORT', 'not set')}")
    logger.info(f"DATABASE_URL: {'configured' if os.getenv('DATABASE_URL') else 'not set'}")
    logger.info(f"RAILWAY_ENVIRONMENT: {os.getenv('RAILWAY_ENVIRONMENT', 'not set')}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)