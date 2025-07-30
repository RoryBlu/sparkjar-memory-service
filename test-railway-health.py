#!/usr/bin/env python3
"""Test script to check Railway health endpoint."""

import os
from fastapi import FastAPI
import uvicorn

# Create a simple app
app = FastAPI(title="Test Memory Service")

@app.get("/")
async def root():
    return {"message": "Memory service root endpoint"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "memory-service-test",
        "port": os.getenv("PORT", "8001"),
        "database_url": "configured" if os.getenv("DATABASE_URL") else "not configured"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)