from pydantic import BaseModel, Field
from typing import List, Any, Dict, Optional
from uuid import UUID

class Observation(BaseModel):
    type: str
    value: Any
    source: str
    metadata: Optional[Dict[str, Any]] = None

class ObservationContent(Observation):
    pass

class ObservationAdd(BaseModel):
    entityName: str
    contents: List[ObservationContent]

class EntityCreate(BaseModel):
    name: str
    entityType: str
    observations: List[Observation] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    aliasOf: Optional[str] = None
    identityConfidence: Optional[float] = None

class RelationCreate(BaseModel):
    from_entity_name: str
    to_entity_name: str
    relationType: str
    metadata: Optional[Dict[str, Any]] = None
