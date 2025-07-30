# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

# memory-service/external_api_hierarchical.py
"""
Enhanced External Memory API with Hierarchical Access Support.

This API extends the standard external memory service to support hierarchical memory access,
while maintaining strict security and backwards compatibility.
"""
from fastapi import FastAPI, Depends, HTTPException, Request, Security, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
import httpx
import jwt
from datetime import datetime, timedelta
import sys
import os
import logging

# Add shared path for schemas

from sparkjar_crew.shared.schemas.memory_schemas import *
from config import settings

logger = logging.getLogger(__name__)

# External API - Secure IPv4/HTTPS with Hierarchical Support
external_app = FastAPI(
    title="SparkJar Memory Service - External (Hierarchical)",
    description="Secure memory API with hierarchical access for external integrations",
    version="2.0.0"
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
        
        # Check hierarchy permissions if present
        if "hierarchy_access" in payload:
            payload["hierarchy_enabled"] = payload["hierarchy_access"]
        
        return payload
        
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# Helper to call internal API
async def call_internal_api(
    endpoint: str, 
    method: str = "POST", 
    json_data: Any = None, 
    token_data: Dict[str, Any] = None,
    query_params: Dict[str, Any] = None
):
    """Call the internal API with proper error handling"""
    internal_url = f"http://[::1]:{settings.INTERNAL_API_PORT}"
    
    # Add auth data to request if provided
    if token_data and json_data:
        json_data["client_id"] = token_data["actor_id"]  # When actor_type="client", this is the client_id
        json_data["actor_type"] = token_data["actor_type"]
        json_data["actor_id"] = token_data["actor_id"]
    
    async with httpx.AsyncClient() as client:
        try:
            url = f"{internal_url}{endpoint}"
            
            if method == "POST":
                response = await client.post(url, json=json_data, params=query_params)
            elif method == "DELETE":
                response = await client.delete(url, json=json_data, params=query_params)
            else:
                response = await client.get(url, params=query_params)
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Internal API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except httpx.RequestError as e:
            logger.error(f"Internal service unavailable: {e}")
            raise HTTPException(status_code=503, detail=f"Internal service unavailable: {str(e)}")

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
async def search_memories_external(
    query: str,
    entity_types: Optional[List[str]] = None,
    limit: int = Query(10, ge=1, le=100),
    include_hierarchy: bool = Query(False, description="Enable hierarchical search"),
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """
    Search memories with optional hierarchical access.
    
    When include_hierarchy=true and the token permits, searches across:
    - Actor's own memories
    - Synth_class templates (for synths)
    - Client-level knowledge (if permitted)
    """
    # Check if hierarchy is allowed for this token
    hierarchy_enabled = include_hierarchy and token_data.get("hierarchy_enabled", False)
    
    request_data = {
        # "client_id" removed - use actor_id when actor_type="client"
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "query": query,
        "entity_type": entity_types,
        "limit": limit
    }
    
    query_params = {"include_hierarchy": hierarchy_enabled}
    
    return await call_internal_api("/search", json_data=request_data, query_params=query_params)

@external_app.post("/memory/hierarchical-search", response_model=List[Dict[str, Any]])
async def hierarchical_search_external(
    query: str,
    entity_types: Optional[List[str]] = None,
    include_synth_class: bool = Query(True, description="Include synth_class memories"),
    include_client: bool = Query(False, description="Include client-level memories"),
    limit: int = Query(10, ge=1, le=100),
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """
    Dedicated hierarchical search endpoint.
    
    Requires explicit hierarchy permissions in the JWT token.
    """
    # Verify hierarchy access is permitted
    if not token_data.get("hierarchy_enabled", False):
        raise HTTPException(
            status_code=403, 
            detail="Hierarchical search not permitted for this token"
        )
    
    request_data = {
        # "client_id" removed - use actor_id when actor_type="client"
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "query": query,
        "entity_type": entity_types,
        "limit": limit
    }
    
    query_params = {
        "include_synth_class": include_synth_class,
        "include_client": include_client
    }
    
    return await call_internal_api("/hierarchical-search", json_data=request_data, query_params=query_params)

@external_app.post("/memory/relations", response_model=List[Dict[str, Any]])
async def create_relations_external(
    relations: List[RelationCreate],
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Create relationships between entities"""
    request_data = {
        # "client_id" removed - use actor_id when actor_type="client"
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "relations": [r.dict() for r in relations]
    }
    
    return await call_internal_api("/relations", json_data=request_data)

@external_app.post("/memory/observations", response_model=List[Dict[str, Any]])
async def add_observations_external(
    observations: List[ObservationAdd],
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Add observations to existing entities"""
    request_data = {
        # "client_id" removed - use actor_id when actor_type="client"
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "observations": [o.dict() for o in observations]
    }
    
    return await call_internal_api("/observations", json_data=request_data)

@external_app.get("/memory/entities", response_model=List[Dict[str, Any]])
async def get_entities_external(
    entity_names: Optional[List[str]] = Query(None),
    entity_types: Optional[List[str]] = Query(None),
    include_hierarchy: bool = Query(False, description="Include hierarchical access"),
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Get specific entities with optional hierarchical access"""
    hierarchy_enabled = include_hierarchy and token_data.get("hierarchy_enabled", False)
    
    request_data = {
        # "client_id" removed - use actor_id when actor_type="client"
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "entity_names": entity_names,
        "entity_types": entity_types
    }
    
    query_params = {"include_hierarchy": hierarchy_enabled}
    
    return await call_internal_api("/get-entities", json_data=request_data, query_params=query_params)

@external_app.delete("/memory/entities", response_model=Dict[str, Any])
async def delete_entities_external(
    entity_names: List[str],
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Delete specific entities (soft delete)"""
    request_data = {
        # "client_id" removed - use actor_id when actor_type="client"
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "entity_names": entity_names
    }
    
    return await call_internal_api("/entities", method="DELETE", json_data=request_data)

@external_app.get("/memory/graph", response_model=Dict[str, Any])
async def read_graph_external(
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Get the complete memory graph for the authenticated actor"""
    request_data = {
        # "client_id" removed - use actor_id when actor_type="client"
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"]
    }
    
    return await call_internal_api("/graph", json_data=request_data)

@external_app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "memory-service-external",
        "version": "2.0.0",
        "features": ["hierarchical-access", "backwards-compatible"]
    }

@external_app.get("/hierarchy-status")
async def hierarchy_status(
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Check if hierarchical access is enabled for this token"""
    return {
        "hierarchy_enabled": token_data.get("hierarchy_enabled", False),
        "actor_type": token_data["actor_type"],
        "features_available": {
            "hierarchical_search": token_data.get("hierarchy_enabled", False),
            "cross_context_access": token_data.get("cross_context_enabled", False)
        }
    }

# Deprecation notices for legacy endpoints
@external_app.post("/memory/open-nodes", response_model=List[Dict[str, Any]], deprecated=True)
async def open_nodes_external(
    names: List[str],
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """
    DEPRECATED: Use GET /memory/entities instead.
    Get specific entities by name.
    """
    logger.warning("Deprecated endpoint /memory/open-nodes called")
    return await get_entities_external(
        entity_names=names,
        token_data=token_data
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        external_app,
        host="0.0.0.0",  # IPv4 for external access
        port=8001,
        ssl_keyfile=settings.SSL_KEY_PATH if hasattr(settings, 'SSL_KEY_PATH') else None,
        ssl_certfile=settings.SSL_CERT_PATH if hasattr(settings, 'SSL_CERT_PATH') else None,
        log_level="info"
    )