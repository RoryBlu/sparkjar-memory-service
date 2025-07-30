#!/usr/bin/env python3
"""Simple internal API for memory service."""

from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import uvicorn
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from database import get_db

# Internal API - IPv6/HTTP
app = FastAPI(
    title="SparkJar Memory Service - Internal",
    description="Internal memory API for service-to-service communication",
    version="1.0.0"
)

# In-memory storage for testing
memory_storage = {
    "entities": {},
    "observations": []
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "memory-internal",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/entities")
async def create_entities(entities: List[Dict[str, Any]]):
    """Create or update entities"""
    created = []
    
    for entity in entities:
        # Generate ID if not provided
        entity_id = entity.get("id", str(datetime.utcnow().timestamp()))
        entity["id"] = entity_id
        
        # Store in memory
        memory_storage["entities"][entity_id] = entity
        created.append(entity)
    
    return created

@app.post("/observations")
async def create_observations(observations: List[Dict[str, Any]]):
    """Create observations"""
    created = []
    
    for obs in observations:
        # Add timestamp
        obs["created_at"] = datetime.utcnow().isoformat()
        memory_storage["observations"].append(obs)
        created.append(obs)
    
    return created

@app.post("/search")
async def search_memories(request: Dict[str, Any]):
    """Search memories"""
    query = request.get("query", "")
    limit = request.get("limit", 10)
    
    # Simple search - return all entities for now
    results = []
    for entity in memory_storage["entities"].values():
        if query.lower() in entity.get("name", "").lower():
            results.append({
                "entity": entity,
                "score": 1.0,
                "context": "TEST"
            })
    
    return results[:limit]

@app.get("/debug/storage")
async def debug_storage():
    """Debug endpoint to see stored data"""
    return {
        "entities_count": len(memory_storage["entities"]),
        "observations_count": len(memory_storage["observations"]),
        "entities": list(memory_storage["entities"].values())[:5],
        "observations": memory_storage["observations"][:5]
    }

if __name__ == "__main__":
    # Kill any existing process on the port
    os.system(f"lsof -ti:{settings.INTERNAL_API_PORT} | xargs kill -9 2>/dev/null || true")
    
    print(f"Starting internal API on port {settings.INTERNAL_API_PORT}...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=settings.INTERNAL_API_PORT,
        log_level="info"
    )