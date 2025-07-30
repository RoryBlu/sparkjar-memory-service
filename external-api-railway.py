# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

#!/usr/bin/env python3
"""External API for Railway deployment - without problematic imports."""

from fastapi import FastAPI, Depends, HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
import httpx
import jwt
from datetime import datetime, timedelta
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models - define inline instead of importing
from pydantic import BaseModel, Field

class EntityCreate(BaseModel):
    name: str
    entityType: str
    metadata: Dict[str, Any] = {}

class RelationCreate(BaseModel):
    fromEntity: str
    toEntity: str
    relationType: str
    metadata: Dict[str, Any] = {}

class ObservationAdd(BaseModel):
    entityName: str
    observationType: str
    content: str
    metadata: Dict[str, Any] = {}

class RelationDelete(BaseModel):
    fromEntity: str
    toEntity: str
    relationType: str

# Configuration
class Settings:
    SECRET_KEY = os.getenv("API_SECRET_KEY", "test-key")
    INTERNAL_API_PORT = int(os.getenv("INTERNAL_API_PORT", "8001"))
    INTERNAL_API_HOST = "localhost"  # Use localhost for internal calls
    EXTERNAL_API_PORT = int(os.getenv("PORT", "8443"))
    EXTERNAL_API_HOST = "0.0.0.0"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60

settings = Settings()

# External API - Secure IPv4/HTTPS
external_app = FastAPI(
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
        # Decode JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        
        # Check expiration
        if datetime.fromtimestamp(payload.get("exp", 0)) < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token expired")
        
        # Check required claims
        if not all(k in payload for k in ["actor_type", "actor_id"  # client_id removed - redundant]):
            raise HTTPException(status_code=401, detail="Invalid token claims")
        
        return payload
        
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# Helper to call internal API
async def call_internal_api(endpoint: str, method: str = "POST", json_data: Any = None, token_data: Dict[str, Any] = None):
    """Call the internal API with proper error handling"""
    internal_url = f"http://{settings.INTERNAL_API_HOST}:{settings.INTERNAL_API_PORT}"
    
    # Add auth data to request if provided
    if token_data and json_data:
        json_data["client_id"] = token_data["actor_id"]  # When actor_type="client", this is the client_id
        json_data["actor_type"] = token_data["actor_type"]
        json_data["actor_id"] = token_data["actor_id"]
    
    async with httpx.AsyncClient() as client:
        try:
            if method == "POST":
                response = await client.post(f"{internal_url}{endpoint}", json=json_data)
            elif method == "DELETE":
                response = await client.delete(f"{internal_url}{endpoint}", json=json_data)
            else:
                response = await client.get(f"{internal_url}{endpoint}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Internal service unavailable: {str(e)}")

@external_app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "memory-external",
        "version": "1.0.0",
        "status": "running",
        "port": settings.EXTERNAL_API_PORT
    }

@external_app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check internal API
        async with httpx.AsyncClient() as client:
            internal_url = f"http://{settings.INTERNAL_API_HOST}:{settings.INTERNAL_API_PORT}/health"
            response = await client.get(internal_url, timeout=2.0)
            internal_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        internal_status = "unreachable"
    
    return {
        "status": "healthy",
        "service": "memory-external",
        "internal_api": internal_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# Endpoints
@external_app.post("/memory/entities", response_model=List[Dict[str, Any]])
async def create_entities_external(
    entities: List[EntityCreate],
    request: Request,
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Create memory entities - authenticated endpoint"""
    request_data = {
        # "client_id" removed - use actor_id when actor_type="client"
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "entities": [e.dict() for e in entities]
    }
    
    return await call_internal_api("/entities", json_data=request_data)

@external_app.post("/memory/search", response_model=List[Dict[str, Any]])
async def search_nodes_external(
    query: str,
    entity_types: Optional[List[str]] = None,
    limit: int = 10,
    min_confidence: float = 0.7,
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Semantic search of memory entities"""
    request_data = {
        # "client_id" removed - use actor_id when actor_type="client"
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "query": query,
        "entity_types": entity_types,
        "limit": limit,
        "min_confidence": min_confidence
    }
    
    return await call_internal_api("/search", json_data=request_data)

# Token generation endpoint (for testing/development)
@external_app.post("/auth/token")
async def create_token(
    # client_id removed - use actor_id when actor_type="client"
    actor_type: str,
    actor_id: UUID,
    api_key: str
):
    """Generate JWT token for API access (development only)"""
    # In production, this should validate api_key against database
    if api_key != settings.SECRET_KEY:  # Simple check for development
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Create token
    expiration = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        # "client_id" removed - use actor_id when actor_type="client"
        "actor_type": actor_type,
        "actor_id": str(actor_id),
        "exp": expiration.timestamp()
    }
    
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@external_app.on_event("startup")
async def startup():
    """Startup event."""
    logger.info("External Memory Service starting up...")
    logger.info(f"Port: {settings.EXTERNAL_API_PORT}")
    logger.info(f"Internal API: {settings.INTERNAL_API_HOST}:{settings.INTERNAL_API_PORT}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(external_app, host="0.0.0.0", port=settings.EXTERNAL_API_PORT)