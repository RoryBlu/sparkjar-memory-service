"""
Unit tests for Sequential Thinking service.
Tests the core business logic without API layer.
"""
import pytest
import asyncio
from uuid import UUID, uuid4
from datetime import datetime, timezone
import sys
import os

from services.thinking_service import ThinkingService
from sparkjar_shared.schemas.thinking_schemas import (
    CreateSessionRequest,
    AddThoughtRequest,
    ReviseThoughtRequest,
    CompleteSessionRequest,
    AbandonSessionRequest,
)

@pytest.fixture
async def thinking_service():
    """Create a ThinkingService instance for testing."""
    service = ThinkingService()
    yield service
    # Cleanup if needed
    if hasattr(service, 'engine'):
        await service.engine.dispose()

@pytest.fixture
def test_user_id():
    """Test user ID."""
    return uuid4()

@pytest.fixture
async def test_session(thinking_service, test_user_id):
    """Create a test session for use in tests."""
    session = await thinking_service.create_session(
        client_user_id=test_user_id,
        session_name="Test Session",
        problem_statement="How to test Sequential Thinking?"
    )
    return session

class TestThinkingService:
    """Test cases for ThinkingService."""
    
    @pytest.mark.asyncio
    async def test_create_session(self, thinking_service, test_user_id):
        """Test creating a new thinking session."""
        # Create session
        result = await thinking_service.create_session(
            client_user_id=test_user_id,
            session_name="Test Problem Solving",
            problem_statement="How do we optimize the API performance?",
            metadata={"priority": "high", "category": "performance"}
        )
        
        # Verify result
        assert result['client_user_id'] == str(test_user_id)
        assert result['session_name'] == "Test Problem Solving"
        assert result['problem_statement'] == "How do we optimize the API performance?"
        assert result['status'] == 'active'
        assert result['metadata']['priority'] == 'high'
        assert result['thoughts'] == []
        assert 'id' in result
        assert 'created_at' in result
    
    @pytest.mark.asyncio
    async def test_add_thought(self, thinking_service, test_session):
        """Test adding thoughts to a session."""
        session_id = UUID(test_session['id'])
        
        # Add first thought
        thought1 = await thinking_service.add_thought(
            session_id=session_id,
            thought_content="We should start by profiling the current API endpoints",
            metadata={"confidence": 0.9}
        )
        
        assert thought1['session_id'] == str(session_id)
        assert thought1['thought_number'] == 1
        assert thought1['thought_content'] == "We should start by profiling the current API endpoints"
        assert thought1['is_revision'] == False
        assert thought1['metadata']['confidence'] == 0.9
        
        # Add second thought
        thought2 = await thinking_service.add_thought(
            session_id=session_id,
            thought_content="Look for N+1 query problems in the database layer"
        )
        
        assert thought2['thought_number'] == 2
        assert thought2['is_revision'] == False
    
    @pytest.mark.asyncio
    async def test_revise_thought(self, thinking_service, test_session):
        """Test revising an existing thought."""
        session_id = UUID(test_session['id'])
        
        # Add initial thoughts
        thought1 = await thinking_service.add_thought(
            session_id=session_id,
            thought_content="Use caching for all endpoints"
        )
        
        thought2 = await thinking_service.add_thought(
            session_id=session_id,
            thought_content="Implement rate limiting"
        )
        
        # Revise first thought
        revision = await thinking_service.revise_thought(
            session_id=session_id,
            thought_number=1,
            revised_content="Use selective caching only for read-heavy endpoints",
            metadata={"reason": "more nuanced approach"}
        )
        
        assert revision['thought_number'] == 3
        assert revision['is_revision'] == True
        assert revision['revises_thought_number'] == 1
        assert revision['thought_content'] == "Use selective caching only for read-heavy endpoints"
    
    @pytest.mark.asyncio
    async def test_complete_session(self, thinking_service, test_session):
        """Test completing a session with final answer."""
        session_id = UUID(test_session['id'])
        
        # Add some thoughts
        await thinking_service.add_thought(
            session_id=session_id,
            thought_content="Profile the API"
        )
        await thinking_service.add_thought(
            session_id=session_id,
            thought_content="Optimize database queries"
        )
        
        # Complete session
        final_answer = """Based on the analysis:
1. Profile API endpoints to identify bottlenecks
2. Optimize database queries by fixing N+1 problems
3. Implement selective caching for read-heavy endpoints"""
        
        result = await thinking_service.complete_session(
            session_id=session_id,
            final_answer=final_answer,
            metadata={"resolved": True}
        )
        
        assert result['status'] == 'completed'
        assert result['final_answer'] == final_answer
        assert 'completed_at' in result
        assert result['metadata']['resolved'] == True
    
    @pytest.mark.asyncio
    async def test_abandon_session(self, thinking_service, test_session):
        """Test abandoning a session."""
        session_id = UUID(test_session['id'])
        
        # Abandon session
        result = await thinking_service.abandon_session(
            session_id=session_id,
            reason="Requirements changed",
            metadata={"new_project": "v2-api"}
        )
        
        assert result['status'] == 'abandoned'
        assert 'completed_at' in result
        assert result['metadata']['abandon_reason'] == "Requirements changed"
        assert result['metadata']['new_project'] == "v2-api"
    
    @pytest.mark.asyncio
    async def test_get_session(self, thinking_service, test_session):
        """Test retrieving a session."""
        session_id = UUID(test_session['id'])
        
        # Add thoughts
        await thinking_service.add_thought(
            session_id=session_id,
            thought_content="First thought"
        )
        await thinking_service.add_thought(
            session_id=session_id,
            thought_content="Second thought"
        )
        
        # Get session with thoughts
        result = await thinking_service.get_session(
            session_id=session_id,
            include_thoughts=True
        )
        
        assert result['id'] == str(session_id)
        assert len(result['thoughts']) == 2
        assert result['thoughts'][0]['thought_content'] == "First thought"
        assert result['thoughts'][1]['thought_content'] == "Second thought"
        
        # Get session without thoughts
        result_no_thoughts = await thinking_service.get_session(
            session_id=session_id,
            include_thoughts=False
        )
        
        assert 'thoughts' not in result_no_thoughts or result_no_thoughts['thoughts'] is None
    
    @pytest.mark.asyncio
    async def test_list_sessions(self, thinking_service, test_user_id):
        """Test listing sessions for a user."""
        # Create multiple sessions
        for i in range(3):
            await thinking_service.create_session(
                client_user_id=test_user_id,
                session_name=f"Session {i+1}",
                problem_statement=f"Problem {i+1}"
            )
        
        # List sessions
        result = await thinking_service.list_sessions(
            client_user_id=test_user_id,
            page=1,
            page_size=10
        )
        
        assert result['total'] >= 3
        assert len(result['sessions']) >= 3
        assert result['page'] == 1
        assert result['page_size'] == 10
        
        # Test pagination
        result_page2 = await thinking_service.list_sessions(
            client_user_id=test_user_id,
            page=2,
            page_size=2
        )
        
        assert result_page2['page'] == 2
        assert result_page2['page_size'] == 2
    
    @pytest.mark.asyncio
    async def test_get_session_stats(self, thinking_service, test_session):
        """Test getting session statistics."""
        session_id = UUID(test_session['id'])
        
        # Add thoughts with revisions
        await thinking_service.add_thought(
            session_id=session_id,
            thought_content="Initial approach"
        )
        await thinking_service.add_thought(
            session_id=session_id,
            thought_content="Secondary consideration"
        )
        await thinking_service.revise_thought(
            session_id=session_id,
            thought_number=1,
            revised_content="Better initial approach"
        )
        
        # Get stats
        stats = await thinking_service.get_session_stats(session_id)
        
        assert stats['session_id'] == str(session_id)
        assert stats['total_thoughts'] == 3
        assert stats['revision_count'] == 1
        assert stats['revised_thought_numbers'] == [1]
        assert stats['average_thought_length'] > 0
        assert 'duration_seconds' in stats
        assert 'thoughts_per_minute' in stats
    
    @pytest.mark.asyncio
    async def test_error_cases(self, thinking_service, test_user_id):
        """Test various error scenarios."""
        # Test adding thought to non-existent session
        with pytest.raises(ValueError, match="not found"):
            await thinking_service.add_thought(
                session_id=uuid4(),
                thought_content="This should fail"
            )
        
        # Test completing already completed session
        session = await thinking_service.create_session(
            client_user_id=test_user_id,
            session_name="Error Test"
        )
        session_id = UUID(session['id'])
        
        await thinking_service.complete_session(
            session_id=session_id,
            final_answer="Done"
        )
        
        with pytest.raises(ValueError, match="already completed"):
            await thinking_service.complete_session(
                session_id=session_id,
                final_answer="Try again"
            )
        
        # Test revising non-existent thought
        active_session = await thinking_service.create_session(
            client_user_id=test_user_id,
            session_name="Another Test"
        )
        active_session_id = UUID(active_session['id'])
        
        with pytest.raises(ValueError, match="not found"):
            await thinking_service.revise_thought(
                session_id=active_session_id,
                thought_number=99,
                revised_content="This should fail"
            )
    
    @pytest.mark.asyncio
    async def test_sequential_thought_numbers(self, thinking_service, test_session):
        """Test that thought numbers are sequential."""
        session_id = UUID(test_session['id'])
        
        # Add multiple thoughts rapidly
        thoughts = []
        for i in range(5):
            thought = await thinking_service.add_thought(
                session_id=session_id,
                thought_content=f"Thought {i+1}"
            )
            thoughts.append(thought)
        
        # Verify sequential numbering
        for i, thought in enumerate(thoughts):
            assert thought['thought_number'] == i + 1
        
        # Add revision and verify it gets next number
        revision = await thinking_service.revise_thought(
            session_id=session_id,
            thought_number=2,
            revised_content="Revised thought 2"
        )
        
        assert revision['thought_number'] == 6
        assert revision['revises_thought_number'] == 2