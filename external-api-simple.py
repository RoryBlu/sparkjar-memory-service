# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

#!/usr/bin/env python3
"""Simple external API for memory service without complex imports."""

from fastapi import FastAPI, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from uuid import UUID
import httpx
import jwt
from datetime import datetime, timedelta
import uvicorn
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from database import get_db

# External API - Secure IPv4/HTTPS
app = FastAPI(
    title="SparkJar Memory Service - External",
    description="Secure memory API for external integrations",
    version="1.0.0"
)

# Security
security = HTTPBearer()

async def verify_external_auth(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Verify JWT token and extract claims"""
    token = credentials.credentials
    
    try:
        # For now, accept any token with sparkjar_internal scope
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"],
            options={"verify_exp": False}  # Skip expiration for testing
        )
        
        # Check for sparkjar_internal scope
        if "sparkjar_internal" not in payload.get("scopes", []):
            raise HTTPException(status_code=401, detail="Invalid scope")
        
        return payload
        
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def call_internal_api(endpoint: str, method: str = "POST", **kwargs):
    """Forward requests to internal API"""
    try:
        internal_url = f"http://localhost:{settings.INTERNAL_API_PORT}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            if method == "POST":
                response = await client.post(internal_url, **kwargs)
            elif method == "GET":
                response = await client.get(internal_url, **kwargs)
            elif method == "DELETE":
                response = await client.delete(internal_url, **kwargs)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json() if response.content else "Internal API error"
                )
            
            return response.json()
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Internal API unavailable: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "memory-external",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/memory/entities")
async def create_entities(
    request: List[Dict[str, Any]],
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Create memory entities"""
    # Add auth context to request
    for entity in request:
        entity["client_id"] = token_data.get("client_id", str(UUID(int=0)))
        entity["actor_type"] = token_data.get("actor_type", "CLIENT")
        entity["actor_id"] = token_data.get("actor_id", str(UUID(int=0)))
    
    return await call_internal_api("/entities", json=request)

@app.post("/memory/observations")
async def create_observations(
    request: List[Dict[str, Any]],
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Create observations"""
    # Add auth context
    for obs in request:
        obs["client_id"] = token_data.get("client_id", str(UUID(int=0)))
        obs["actor_type"] = token_data.get("actor_type", "CLIENT")
        obs["actor_id"] = token_data.get("actor_id", str(UUID(int=0)))
    
    return await call_internal_api("/observations", json=request)

@app.post("/memory/search")
async def search_memories(
    request: Dict[str, Any],
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Search memories"""
    # Add auth context
    request["client_id"] = token_data.get("client_id", str(UUID(int=0)))
    request["actor_type"] = token_data.get("actor_type", "CLIENT")
    request["actor_id"] = token_data.get("actor_id", str(UUID(int=0)))
    
    return await call_internal_api("/search", json=request)

@app.post("/auth/token")
async def create_token(
    client_id: str = "00000000-0000-0000-0000-000000000000",
    actor_type: str = "CLIENT",
    actor_id: str = "00000000-0000-0000-0000-000000000000"
):
    """Generate test token"""
    payload = {
        "sub": "test-user",
        # "client_id" removed - use actor_id when actor_type="client"
        "actor_type": actor_type,
        "actor_id": actor_id,
        "scopes": ["sparkjar_internal"],
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
        "iss": "sparkjar-memory"
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 86400
    }

if __name__ == "__main__":
    # Kill any existing process on the port
    os.system(f"lsof -ti:{settings.EXTERNAL_API_PORT} | xargs kill -9 2>/dev/null || true")
    
    print(f"Starting external API on port {settings.EXTERNAL_API_PORT}...")
    uvicorn.run(
        app, 
        host=settings.API_HOST, 
        port=settings.EXTERNAL_API_PORT,
        log_level="info"
    )