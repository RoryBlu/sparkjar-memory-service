# memory-service/internal_api.py
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID
import json
import sys
import os

# Add shared path for schemas

from database import get_db
from services.memory_manager import MemoryManager
from services.embeddings import EmbeddingService
# from sparkjar_crew.shared.schemas.memory_schemas import *  # REMOVED - doesn't exist in this repo
# Define schemas inline instead
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from config import settings

# Schema definitions
class EntityCreate(BaseModel):
    name: str
    entityType: str
    metadata: Dict[str, Any] = {}

class CreateEntitiesRequest(BaseModel):
    client_id: UUID
    actor_type: str
    actor_id: UUID
    entities: List[EntityCreate]

class RelationCreate(BaseModel):
    fromEntity: str
    toEntity: str
    relationType: str
    metadata: Dict[str, Any] = {}

class CreateRelationsRequest(BaseModel):
    client_id: UUID
    actor_type: str
    actor_id: UUID
    relations: List[RelationCreate]

class ObservationAdd(BaseModel):
    entityName: str
    observationType: str
    content: str
    metadata: Dict[str, Any] = {}

class AddObservationsRequest(BaseModel):
    client_id: UUID
    actor_type: str
    actor_id: UUID
    observations: List[ObservationAdd]

class SearchRequest(BaseModel):
    client_id: UUID
    actor_type: str
    actor_id: UUID
    query: str
    entity_type: Optional[str] = None
    limit: int = 10
    threshold: float = 0.7

class OpenNodesRequest(BaseModel):
    client_id: UUID
    actor_type: str
    actor_id: UUID
    names: List[str]

class ReadGraphRequest(BaseModel):
    client_id: UUID
    actor_type: str
    actor_id: UUID

class DeleteEntitiesRequest(BaseModel):
    client_id: UUID
    actor_type: str
    actor_id: UUID
    entity_names: List[str]

class DeleteRelationsRequest(BaseModel):
    client_id: UUID
    actor_type: str
    actor_id: UUID
    relations: List[RelationCreate]

class RememberConversationRequest(BaseModel):
    client_id: UUID
    actor_type: str
    actor_id: UUID
    conversation_text: str
    participants: List[str]
    context: Dict[str, Any] = {}

class FindConnectionsRequest(BaseModel):
    client_id: UUID
    actor_type: str
    actor_id: UUID
    from_entity: str
    to_entity: Optional[str] = None
    max_hops: int = 3
    relationship_types: Optional[List[str]] = None

class GetClientInsightsRequest(BaseModel):
    client_id: UUID
    actor_type: str
    actor_id: UUID

class ProcessTextChunkRequest(BaseModel):
    client_id: UUID
    actor_type: str
    actor_id: UUID
    text: str
    source: str
    extract_context: bool = True
    context_preview_length: int = 100

# Internal API - High Performance IPv6/HTTP
internal_app = FastAPI(
    title="SparkJar Memory Service - Internal",
    description="High-performance memory API for internal services",
    version="1.0.0"
)

def get_memory_manager(db: Session = Depends(get_db)) -> MemoryManager:
    """Dependency to get memory manager instance"""
    embedding_service = EmbeddingService(
        api_url=settings.EMBEDDINGS_API_URL,
        model=settings.EMBEDDING_MODEL,
        dimension=int(settings.EMBEDDING_DIMENSION)
    )
    return MemoryManager(db, embedding_service)

@internal_app.post("/entities", response_model=List[Dict[str, Any]])
async def create_entities_internal(
    request: CreateEntitiesRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Create multiple entities - internal high-speed endpoint"""
    try:
        result = await memory_manager.create_entities(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            entities=request.entities
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Entity creation failed: {str(e)}")

@internal_app.post("/relations", response_model=List[Dict[str, Any]]) 
async def create_relations_internal(
    request: CreateRelationsRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Create relationships between entities"""
    try:
        result = await memory_manager.create_relations(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            relations=request.relations
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Relation creation failed: {str(e)}")

@internal_app.post("/observations", response_model=List[Dict[str, Any]])
async def add_observations_internal(
    request: AddObservationsRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Add observations to existing entities"""
    try:
        result = await memory_manager.add_observations(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            observations=request.observations
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adding observations failed: {str(e)}")

@internal_app.post("/search", response_model=List[Dict[str, Any]])
async def search_nodes_internal(
    request: SearchRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Semantic search of memory entities"""
    try:
        result = await memory_manager.search_nodes(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            query=request.query,
            entity_type=request.entity_type,
            limit=request.limit,
            threshold=request.threshold
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@internal_app.post("/nodes", response_model=List[Dict[str, Any]])
async def open_nodes_internal(
    request: OpenNodesRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Get specific entities by name"""
    try:
        result = await memory_manager.open_nodes(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            names=request.names
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Open nodes failed: {str(e)}")

@internal_app.post("/graph", response_model=Dict[str, Any])
async def read_graph_internal(
    request: ReadGraphRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Get all entities and relations for an actor"""
    try:
        result = await memory_manager.read_graph(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Read graph failed: {str(e)}")

@internal_app.delete("/entities", response_model=Dict[str, Any])
async def delete_entities_internal(
    request: DeleteEntitiesRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Soft delete entities and their relations"""
    try:
        result = await memory_manager.delete_entities(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            entity_names=request.entity_names
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete entities failed: {str(e)}")

@internal_app.delete("/relations", response_model=Dict[str, Any])
async def delete_relations_internal(
    request: DeleteRelationsRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Delete specific relations"""
    try:
        result = await memory_manager.delete_relations(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            relations=request.relations
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete relations failed: {str(e)}")

# SparkJar-specific endpoints
@internal_app.post("/remember_conversation", response_model=Dict[str, Any])
async def remember_conversation_internal(
    request: RememberConversationRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Extract and store knowledge from conversation transcripts"""
    try:
        result = await memory_manager.remember_conversation(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            conversation_text=request.conversation_text,
            participants=request.participants,
            context=request.context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Remember conversation failed: {str(e)}")

@internal_app.post("/find_connections", response_model=Dict[str, Any])
async def find_connections_internal(
    request: FindConnectionsRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Find paths between entities"""
    try:
        result = await memory_manager.find_connections(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            from_entity=request.from_entity,
            to_entity=request.to_entity,
            max_hops=request.max_hops,
            relationship_types=request.relationship_types
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Find connections failed: {str(e)}")

@internal_app.post("/insights", response_model=Dict[str, Any])
async def get_client_insights_internal(
    request: GetClientInsightsRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Generate insights about the client's knowledge graph"""
    try:
        result = await memory_manager.get_client_insights(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get insights failed: {str(e)}")

@internal_app.post("/process_text_chunk", response_model=Dict[str, Any])
async def process_text_chunk_internal(
    request: ProcessTextChunkRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """
    Process a text chunk into entities, observations, and relationships.
    Uses GPT-4.1-nano for extraction with context from existing memories.
    """
    try:
        result = await memory_manager.process_text_chunk(
            client_id=request.client_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            text=request.text,
            source=request.source,
            extract_context=request.extract_context,
            context_preview_length=request.context_preview_length
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Process text chunk failed: {str(e)}")

# Import and include thinking routes - DISABLED for Railway
# from api.thinking_routes import router as thinking_router
# internal_app.include_router(thinking_router, prefix="/api/v1")