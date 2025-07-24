# tests/conftest.py
import pytest
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import sys
from uuid import uuid4
from datetime import datetime

# Add parent directories to path

from services.memory_manager import MemoryManager
from services.embeddings import EmbeddingService
from services.thinking_service import ThinkingService
from database import get_db

# Test database configuration
TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL', os.getenv('DATABASE_URL'))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    # Use sync URL for testing
    sync_url = TEST_DATABASE_URL.replace('+asyncpg', '').replace('?pgbouncer=true', '')
    engine = create_engine(sync_url)
    
    # Clean up test data before tests
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM memory_relations WHERE client_id = '11111111-1111-1111-1111-111111111111'"))
        conn.execute(text("DELETE FROM memory_entities WHERE client_id = '11111111-1111-1111-1111-111111111111'"))
        conn.commit()
    
    yield engine
    
    # Clean up after tests
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM memory_relations WHERE client_id = '11111111-1111-1111-1111-111111111111'"))
        conn.execute(text("DELETE FROM memory_entities WHERE client_id = '11111111-1111-1111-1111-111111111111'"))
        conn.commit()

@pytest.fixture
def db_session(test_engine):
    """Create a test database session"""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def embedding_service():
    """Real embedding service for integration tests"""
    from services.embeddings import EmbeddingService
    from config import settings
    import os
    
    # Use test URL if available, otherwise fall back to internal
    api_url = os.getenv('EMBEDDINGS_API_URL_TEST', settings.EMBEDDINGS_API_URL)
    
    return EmbeddingService(
        api_url=api_url,
        model=settings.EMBEDDING_MODEL,
        dimension=int(settings.EMBEDDING_DIMENSION)
    )

@pytest.fixture
def memory_manager(db_session, embedding_service):
    """Create a memory manager instance for testing"""
    return MemoryManager(db_session, embedding_service)

@pytest.fixture
async def thinking_service():
    """Create a thinking service instance for testing"""
    service = ThinkingService()
    yield service
    # Cleanup is handled by the service's session management

@pytest.fixture
def test_context():
    """Standard test context for multi-tenant operations"""
    return {
        "client_id": uuid4(),  # Use random UUID for isolation
        "actor_type": "human",
        "actor_id": uuid4()
    }

@pytest.fixture
def sample_entities():
    """Sample entity data for testing"""
    return [
        {
            "name": "John Doe",
            "entityType": "person",
            "observations": [
                {
                    "type": "skill",
                    "value": {
                        "name": "Python Programming",
                        "category": "technical",
                        "level": "expert"
                    },
                    "source": "code_review"
                },
                {
                    "type": "fact",
                    "value": "Senior Engineer at TechCorp",
                    "source": "profile"
                }
            ],
            "metadata": {
                "role": "Senior Engineer",
                "organization": "TechCorp",
                "email": "john.doe@techcorp.com"
            }
        },
        {
            "name": "AI Assistant",
            "entityType": "synth",
            "observations": [
                {
                    "type": "skill",
                    "value": {
                        "name": "Natural Language Processing",
                        "category": "technical",
                        "level": "advanced"
                    },
                    "source": "configuration"
                }
            ],
            "metadata": {
                "agent_type": "ai_assistant",
                "model_name": "gpt-4",
                "capabilities": ["chat", "analysis", "code_generation"]
            }
        }
    ]

@pytest.fixture
def sample_relations():
    """Sample relation data for testing"""
    return [
        {
            "from_entity_name": "John Doe",
            "to_entity_name": "AI Assistant",
            "relationType": "manages",
            "metadata": {"since": "2024-01-01"}
        }
    ]