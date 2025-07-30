# memory-service/external_api.py
from fastapi import FastAPI, Depends, HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
import httpx
import jwt
from datetime import datetime, timedelta
import sys
import os

# Add shared path for schemas
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Skip the problematic import - define what we need inline
# from sparkjar_crew.shared.schemas.memory_schemas import *  # REMOVED - doesn't exist in this repo
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID

# Import config
try:
    from config import Settings
    settings = Settings()
except:
    # Fallback settings
    class Settings:
        SECRET_KEY = os.getenv("API_SECRET_KEY", "test-key")
        INTERNAL_API_PORT = int(os.getenv("INTERNAL_API_PORT", "8001"))
        INTERNAL_API_HOST = "::"
        EXTERNAL_API_PORT = int(os.getenv("EXTERNAL_API_PORT", "8443"))
        EXTERNAL_API_HOST = "0.0.0.0"
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
        if not all(k in payload for k in ["client_id", "actor_type", "actor_id"]):
            raise HTTPException(status_code=401, detail="Invalid token claims")
        
        return payload
        
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# Helper to call internal API
async def call_internal_api(endpoint: str, method: str = "POST", json_data: Any = None, token_data: Dict[str, Any] = None):
    """Call the internal API with proper error handling"""
    internal_url = f"http://[::1]:{settings.INTERNAL_API_PORT}"
    
    # Add auth data to request if provided
    if token_data and json_data:
        json_data["client_id"] = token_data["client_id"]
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

# Endpoints
@external_app.post("/memory/entities", response_model=List[Dict[str, Any]])
async def create_entities_external(
    entities: List[EntityCreate],
    request: Request,
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Create memory entities - authenticated endpoint"""
    # Add rate limiting check here if needed
    
    request_data = {
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "entities": [e.dict() for e in entities]
    }
    
    return await call_internal_api("/entities", json_data=request_data)

@external_app.post("/memory/relations", response_model=List[Dict[str, Any]])
async def create_relations_external(
    relations: List[RelationCreate],
    request: Request,
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Create relationships between entities"""
    request_data = {
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "relations": [r.dict() for r in relations]
    }
    
    return await call_internal_api("/relations", json_data=request_data)

@external_app.post("/memory/observations", response_model=List[Dict[str, Any]])
async def add_observations_external(
    observations: List[ObservationAdd],
    request: Request,
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Add observations to existing entities"""
    request_data = {
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "observations": [o.dict() for o in observations]
    }
    
    return await call_internal_api("/observations", json_data=request_data)

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
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "query": query,
        "entity_types": entity_types,
        "limit": limit,
        "min_confidence": min_confidence
    }
    
    return await call_internal_api("/search", json_data=request_data)

@external_app.post("/memory/nodes", response_model=List[Dict[str, Any]])
async def open_nodes_external(
    names: List[str],
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Get specific entities by name"""
    request_data = {
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "names": names
    }
    
    return await call_internal_api("/nodes", json_data=request_data)

@external_app.get("/memory/graph", response_model=Dict[str, Any])
async def read_graph_external(
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Get all entities and relations for the authenticated actor"""
    request_data = {
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"]
    }
    
    return await call_internal_api("/graph", json_data=request_data)

@external_app.delete("/memory/entities", response_model=Dict[str, Any])
async def delete_entities_external(
    entity_names: List[str],
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Soft delete entities and their relations"""
    request_data = {
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "entity_names": entity_names
    }
    
    return await call_internal_api("/entities", method="DELETE", json_data=request_data)

@external_app.delete("/memory/relations", response_model=Dict[str, Any])
async def delete_relations_external(
    relations: List[RelationDelete],
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Delete specific relations"""
    request_data = {
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "relations": [r.dict() for r in relations]
    }
    
    return await call_internal_api("/relations", method="DELETE", json_data=request_data)

# SparkJar-specific endpoints
@external_app.post("/memory/remember_conversation", response_model=Dict[str, Any])
async def remember_conversation_external(
    conversation_text: str,
    participants: List[str],
    context: Dict[str, Any] = {},
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Extract and store knowledge from conversation transcripts"""
    request_data = {
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "conversation_text": conversation_text,
        "participants": participants,
        "context": context
    }
    
    return await call_internal_api("/remember_conversation", json_data=request_data)

@external_app.post("/memory/find_connections", response_model=Dict[str, Any])
async def find_connections_external(
    from_entity: str,
    to_entity: Optional[str] = None,
    max_hops: int = 3,
    relationship_types: Optional[List[str]] = None,
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Find paths between entities"""
    request_data = {
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "from_entity": from_entity,
        "to_entity": to_entity,
        "max_hops": max_hops,
        "relationship_types": relationship_types
    }
    
    return await call_internal_api("/find_connections", json_data=request_data)

@external_app.get("/memory/insights", response_model=Dict[str, Any])
async def get_client_insights_external(
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Generate insights about the client's knowledge graph"""
    request_data = {
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"]
    }
    
    return await call_internal_api("/insights", method="POST", json_data=request_data)

@external_app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check internal API
        async with httpx.AsyncClient() as client:
            internal_url = f"http://[::1]:{settings.INTERNAL_API_PORT}/docs"
            response = await client.get(internal_url, timeout=2.0)
            internal_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        internal_status = "unreachable"
    
    return {
        "status": "healthy",
        "internal_api": internal_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# Token generation endpoint (for testing/development)
@external_app.post("/auth/token")
async def create_token(
    client_id: UUID,
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
        "client_id": str(client_id),
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

# Import and include thinking routes - DISABLED for Railway
# from api.thinking_routes import router as thinking_router
# external_app.include_router(thinking_router, prefix="/api/v1")