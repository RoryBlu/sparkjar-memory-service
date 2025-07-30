#!/usr/bin/env python3
"""Unified external API with optional simplified auth."""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt

from config import settings

external_app = FastAPI(
    title="SparkJar Memory Service - External",
    description="Secure memory API for external integrations",
    version="1.0.0",
)

security = HTTPBearer()

async def verify_external_auth(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if datetime.fromtimestamp(payload.get("exp", 0)) < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


async def call_internal_api(endpoint: str, method: str = "POST", json_data: Any = None):
    url = f"http://{settings.INTERNAL_API_HOST}:{settings.INTERNAL_API_PORT}{endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            if method == "POST":
                resp = await client.post(url, json=json_data)
            elif method == "GET":
                resp = await client.get(url, timeout=5.0)
            else:
                resp = await client.delete(url, json=json_data)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Internal API unavailable: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)


@external_app.get("/health")
async def health_check():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"http://{settings.INTERNAL_API_HOST}:{settings.INTERNAL_API_PORT}/health", timeout=2.0)
            internal_status = "healthy" if resp.status_code == 200 else "unhealthy"
    except Exception:
        internal_status = "unreachable"
    return {
        "status": "healthy",
        "service": "memory-external",
        "internal_api": internal_status,
        "timestamp": datetime.utcnow().isoformat(),
    }


@external_app.post("/memory/entities")
async def create_entities_external(
    entities: List[Dict[str, Any]],
    token_data: Dict[str, Any] = Depends(verify_external_auth),
):
    for entity in entities:
        entity["client_id"] = token_data.get("client_id", str(UUID(int=0)))
        entity["actor_type"] = token_data.get("actor_type", "CLIENT")
        entity["actor_id"] = token_data.get("actor_id", str(UUID(int=0)))
    return await call_internal_api("/entities", json_data=entities)


@external_app.post("/memory/search")
async def search_memories_external(
    request: Dict[str, Any],
    token_data: Dict[str, Any] = Depends(verify_external_auth),
):
    request["client_id"] = token_data.get("client_id", str(UUID(int=0)))
    request["actor_type"] = token_data.get("actor_type", "CLIENT")
    request["actor_id"] = token_data.get("actor_id", str(UUID(int=0)))
    return await call_internal_api("/search", json_data=request)


@external_app.post("/auth/token")
async def create_token(
    client_id: UUID,
    actor_type: str,
    actor_id: UUID,
    api_key: Optional[str] = None,
):
    if api_key != settings.SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    expiration = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "client_id": str(client_id),
        "actor_type": actor_type,
        "actor_id": str(actor_id),
        "exp": expiration.timestamp(),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@external_app.on_event("startup")
async def startup():
    logging.getLogger(__name__).info("External API starting up")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(external_app, host="0.0.0.0", port=settings.EXTERNAL_API_PORT)
