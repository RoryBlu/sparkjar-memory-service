from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.types import JSON
from uuid import uuid4
from datetime import datetime

Base = declarative_base()

class MemoryEntities(Base):
    __tablename__ = 'memory_entities'
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    client_id = Column(String, index=True)
    actor_type = Column(String)
    actor_id = Column(String)
    entity_name = Column(String, index=True)
    entity_type = Column(String)
    embedding = Column(JSON)
    metadata_json = Column(JSON, default=dict)
    alias_of = Column(String, nullable=True)
    identity_confidence = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

class MemoryObservations(Base):
    __tablename__ = 'memory_observations'
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    entity_id = Column(String, ForeignKey('memory_entities.id'))
    observation_type = Column(String)
    observation_value = Column(JSON)
    source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class MemoryRelations(Base):
    __tablename__ = 'memory_relations'
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    client_id = Column(String, index=True)
    actor_type = Column(String)
    actor_id = Column(String)
    from_entity_id = Column(String, ForeignKey('memory_entities.id'))
    to_entity_id = Column(String, ForeignKey('memory_entities.id'))
    from_entity_name = Column(String)
    to_entity_name = Column(String)
    relation_type = Column(String)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

class ObjectSchemas(Base):
    __tablename__ = 'object_schemas'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    object_type = Column(String)
    schema = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
