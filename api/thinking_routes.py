"""
API routes for Sequential Thinking feature.
Provides endpoints for managing thinking sessions and thoughts.
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional, Dict, Any
from uuid import UUID
import logging

import sys
import os

from services.thinking_service import ThinkingService
from sparkjar_crew.shared.schemas.thinking_schemas import (
    CreateSessionRequest,
    AddThoughtRequest,
    ReviseThoughtRequest,
    CompleteSessionRequest,
    AbandonSessionRequest,
    SessionResponse,
    ThoughtResponse,
    SessionListResponse,
    SessionStatsResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/thinking",
    tags=["thinking"],
    responses={
        404: {"model": ErrorResponse, "description": "Resource not found"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)

# Initialize service
thinking_service = ThinkingService()

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(request: CreateSessionRequest) -> SessionResponse:
    """
    Create a new thinking session.
    
    Args:
        request: Session creation request
        
    Returns:
        Created session details
    """
    try:
        result = await thinking_service.create_session(
            client_user_id=request.client_user_id,
            session_name=request.session_name,
            problem_statement=request.problem_statement,
            metadata=request.metadata
        )
        return SessionResponse(**result)
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    include_thoughts: bool = True
) -> SessionResponse:
    """
    Get a thinking session by ID.
    
    Args:
        session_id: Session ID
        include_thoughts: Whether to include thoughts
        
    Returns:
        Session details
    """
    try:
        result = await thinking_service.get_session(
            session_id=session_id,
            include_thoughts=include_thoughts
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        return SessionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/users/{client_user_id}/sessions", response_model=SessionListResponse)
async def list_sessions(
    client_user_id: UUID,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
) -> SessionListResponse:
    """
    List thinking sessions for a user.
    
    Args:
        client_user_id: User ID
        status: Optional status filter (active, completed, abandoned)
        page: Page number (1-based)
        page_size: Items per page
        
    Returns:
        Paginated list of sessions
    """
    try:
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be >= 1"
            )
        
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )
        
        if status and status not in ['active', 'completed', 'abandoned']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be one of: active, completed, abandoned"
            )
        
        result = await thinking_service.list_sessions(
            client_user_id=client_user_id,
            status=status,
            page=page,
            page_size=page_size
        )
        
        return SessionListResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/sessions/{session_id}/thoughts", response_model=ThoughtResponse)
async def add_thought(
    session_id: UUID,
    request: AddThoughtRequest
) -> ThoughtResponse:
    """
    Add a thought to an active session.
    
    Args:
        session_id: Session ID
        request: Thought content and metadata
        
    Returns:
        Created thought details
    """
    try:
        result = await thinking_service.add_thought(
            session_id=session_id,
            thought_content=request.thought_content,
            metadata=request.metadata
        )
        
        return ThoughtResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding thought: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/sessions/{session_id}/revise", response_model=ThoughtResponse)
async def revise_thought(
    session_id: UUID,
    request: ReviseThoughtRequest
) -> ThoughtResponse:
    """
    Revise an existing thought in the session.
    
    Args:
        session_id: Session ID
        request: Revision details
        
    Returns:
        Created revision details
    """
    try:
        result = await thinking_service.revise_thought(
            session_id=session_id,
            thought_number=request.thought_number,
            revised_content=request.revised_content,
            metadata=request.metadata
        )
        
        return ThoughtResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error revising thought: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/sessions/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: UUID,
    request: CompleteSessionRequest
) -> SessionResponse:
    """
    Complete a thinking session with final answer.
    
    Args:
        session_id: Session ID
        request: Final answer and metadata
        
    Returns:
        Updated session details
    """
    try:
        result = await thinking_service.complete_session(
            session_id=session_id,
            final_answer=request.final_answer,
            metadata=request.metadata
        )
        
        # Get full session with thoughts for response
        full_session = await thinking_service.get_session(
            session_id=session_id,
            include_thoughts=True
        )
        
        return SessionResponse(**full_session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error completing session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/sessions/{session_id}/abandon", response_model=SessionResponse)
async def abandon_session(
    session_id: UUID,
    request: AbandonSessionRequest
) -> SessionResponse:
    """
    Abandon a thinking session.
    
    Args:
        session_id: Session ID
        request: Abandonment reason and metadata
        
    Returns:
        Updated session details
    """
    try:
        result = await thinking_service.abandon_session(
            session_id=session_id,
            reason=request.reason,
            metadata=request.metadata
        )
        
        # Get full session for response
        full_session = await thinking_service.get_session(
            session_id=session_id,
            include_thoughts=False
        )
        
        return SessionResponse(**full_session)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error abandoning session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/sessions/{session_id}/stats", response_model=SessionStatsResponse)
async def get_session_stats(session_id: UUID) -> SessionStatsResponse:
    """
    Get statistics for a thinking session.
    
    Args:
        session_id: Session ID
        
    Returns:
        Session statistics
    """
    try:
        result = await thinking_service.get_session_stats(session_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        return SessionStatsResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Health check endpoint
@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    Check if the thinking service is healthy.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "sequential-thinking",
        "version": "1.0.0"
    }