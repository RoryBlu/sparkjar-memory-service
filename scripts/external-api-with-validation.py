# memory-service/external_api_with_validation.py
from fastapi import FastAPI, Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
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

# External API - Secure IPv4/HTTPS
external_app = FastAPI(
    title="SparkJar Memory Service - External",
    description="Secure memory API for external integrations with actor validation",
    version="1.1.0"
)

# Security
security = HTTPBearer()

# Valid actor types for validation
VALID_ACTOR_TYPES = {'human', 'synth', 'synth_class', 'client', 'skill_module'}

async def verify_external_auth(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Verify JWT token and extract claims with actor type validation"""
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
        
        # Validate actor_type
        actor_type = payload.get("actor_type")
        if actor_type not in VALID_ACTOR_TYPES:
            raise HTTPException(
                status_code=401, 
                detail=f"Invalid actor_type in token: '{actor_type}'. Valid types: {', '.join(VALID_ACTOR_TYPES)}"
            )
        
        return payload
        
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# Helper to call internal API
async def call_internal_api(
    endpoint: str, 
    method: str = "POST", 
    json_data: Any = None, 
    token_data: Dict[str, Any] = None
):
    """Call the internal API with proper error handling"""
    # Use internal service name for IPv6 on Railway
    internal_url = f"http://memory-internal.railway.internal:{settings.INTERNAL_API_PORT}"
    
    # Fallback to localhost for local development
    if settings.ENVIRONMENT == "development":
        internal_url = f"http://localhost:{settings.INTERNAL_API_PORT}"
    
    # Add auth data to request if provided
    if token_data and json_data:
        json_data["client_id"] = token_data["client_id"]
        json_data["actor_type"] = token_data["actor_type"]
        json_data["actor_id"] = token_data["actor_id"]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method == "POST":
                response = await client.post(f"{internal_url}{endpoint}", json=json_data)
            elif method == "DELETE":
                response = await client.delete(f"{internal_url}{endpoint}", json=json_data)
            else:
                response = await client.get(f"{internal_url}{endpoint}")
            
            # Handle validation errors from internal API
            if response.status_code == 400:
                error_detail = response.json()
                if isinstance(error_detail, dict) and error_detail.get("code") == "MEM-102":
                    # Actor validation failed
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error_detail
                    )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            # Parse error response from internal API
            try:
                error_detail = e.response.json()
                raise HTTPException(
                    status_code=e.response.status_code, 
                    detail=error_detail
                )
            except:
                raise HTTPException(
                    status_code=e.response.status_code, 
                    detail=e.response.text
                )
        except httpx.RequestError as e:
            logger.error(f"Internal service connection failed: {e}")
            raise HTTPException(
                status_code=503, 
                detail=f"Internal service unavailable: {str(e)}"
            )

# Error response model
class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

# Endpoints
@external_app.post("/memory/entities/upsert", response_model=List[Dict[str, Any]])
async def upsert_entities_external(
    entities: List[EntityCreate],
    skill_module_id: Optional[UUID] = None,
    request: Request,
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """
    Upsert memory entities with optional skill module context.
    
    When skill_module_id is provided and the actor is a synth, memories
    are created in the skill module context rather than the synth's direct context.
    The synth must be subscribed to the skill module.
    """
    request_data = {
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "entities": [e.dict() for e in entities]
    }
    
    # Build URL with optional skill_module_id parameter
    url = "/entities/upsert"
    if skill_module_id:
        url += f"?skill_module_id={skill_module_id}"
    
    return await call_internal_api(url, json_data=request_data)

@external_app.post("/memory/entities", response_model=List[Dict[str, Any]])
async def create_entities_external(
    entities: List[EntityCreate],
    request: Request,
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Create memory entities - authenticated endpoint with validation"""
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
    """Create relationships between entities - authenticated endpoint"""
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
    """Add observations to entities - authenticated endpoint"""
    request_data = {
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "observations": [o.dict() for o in observations]
    }
    
    return await call_internal_api("/observations", json_data=request_data)

@external_app.post("/memory/search", response_model=List[Dict[str, Any]])
async def search_memory_external(
    query: str,
    entity_type: Optional[str] = None,
    limit: int = 10,
    token_data: Dict[str, Any] = Depends(verify_external_auth)
):
    """Search memory - authenticated endpoint"""
    request_data = {
        "client_id": token_data["client_id"],
        "actor_type": token_data["actor_type"],
        "actor_id": token_data["actor_id"],
        "query": query,
        "entity_type": entity_type,
        "limit": limit
    }
    
    return await call_internal_api("/search", json_data=request_data)

@external_app.get("/health")
async def health_check_external():
    """Health check endpoint for external API"""
    # Check internal API health
    try:
        await call_internal_api("/health", method="GET")
        internal_healthy = True
    except:
        internal_healthy = False
    
    return {
        "status": "healthy" if internal_healthy else "degraded",
        "service": "memory-service-external",
        "version": "1.1.0",
        "features": ["actor_validation", "jwt_auth"],
        "internal_api": "healthy" if internal_healthy else "unreachable"
    }

@external_app.get("/actor-types")
async def get_valid_actor_types():
    """Get list of valid actor types for reference"""
    return {
        "actor_types": list(VALID_ACTOR_TYPES),
        "descriptions": {
            "human": "Human users (references client_users table)",
            "synth": "AI agents/personas (references synths table)",
            "synth_class": "AI agent templates (references synth_classes table)",
            "client": "Organizations (references clients table)",
            "skill_module": "Skill modules/capabilities (references skill_modules table)"
        }
    }

# Startup event
@external_app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("Memory Service External API starting...")
    logger.info("Actor validation enabled via JWT claims")
    logger.info("Valid actor types: %s", ", ".join(VALID_ACTOR_TYPES))

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        external_app,
        host="0.0.0.0",  # Bind to all interfaces
        port=8443,
        log_level="info"
    )