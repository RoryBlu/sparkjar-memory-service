import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from sparkjar_crew.shared.database.models import Base
from sparkjar_shared.schemas.memory_schemas import EntityCreate, Observation
from services.memory_manager import MemoryManager
import services.memory_manager as mm


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def memory_manager(db_session, mock_embedding_service):
    return MemoryManager(db_session, mock_embedding_service)


@pytest.mark.asyncio
async def test_cod_ingest_and_retrieve(memory_manager, monkeypatch):
    actor_type = "client"
    actor_id = str(uuid4())
    mm.client_id = actor_id
    monkeypatch.setattr(mm, "uuid4", lambda: str(uuid4()))

    entity = EntityCreate(
        name="CoD Test",
        entityType="cod",
        observations=[Observation(type="fact", value="demo", source="test")],
    )

    created = await memory_manager.create_entities(
        actor_type,
        actor_id,
        [entity],
    )
    assert len(created) == 1

    result = await memory_manager.open_nodes(
        actor_type,
        actor_id,
        ["CoD Test"],
    )
    assert len(result) == 1
    assert result[0]["entity_name"] == "CoD Test"
