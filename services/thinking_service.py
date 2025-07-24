"""
Sequential Thinking Service - Core business logic for the thinking feature.
Handles session management, thought tracking, and revision logic.
"""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, and_, func, text, Column, Integer, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import selectinload, declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from sparkjar_crew.shared.config.config import DATABASE_URL_DIRECT
from sparkjar_crew.shared.services.schema_validator import ThinkingSchemaValidator

logger = logging.getLogger(__name__)

# Define models locally to avoid import issues
Base = declarative_base()

class ThinkingSessions(Base):
    __tablename__ = "thinking_sessions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'))
    client_user_id = Column(PGUUID(as_uuid=True), nullable=False)
    session_name = Column(Text)
    problem_statement = Column(Text)
    status = Column(Text, nullable=False, server_default='active')
    final_answer = Column(Text)
    metadata_json = Column('metadata', JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

class Thoughts(Base):
    __tablename__ = "thoughts"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, nullable=False, server_default=text('gen_random_uuid()'))
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("thinking_sessions.id"), nullable=False)
    thought_number = Column(Integer, nullable=False)
    thought_content = Column(Text, nullable=False)
    is_revision = Column(Boolean, nullable=False)
    revises_thought_number = Column(Integer)
    metadata_json = Column('metadata', JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

# Relationships
ThinkingSessions.thoughts = relationship("Thoughts", back_populates="session", cascade="all, delete-orphan")
Thoughts.session = relationship("ThinkingSessions", back_populates="thoughts")

class ThinkingService:
    """Service for managing Sequential Thinking sessions and thoughts."""
    
    def __init__(self):
        """Initialize the ThinkingService."""
        self.engine = create_async_engine(
            DATABASE_URL_DIRECT,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        self.async_session = async_sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        self.schema_validator = None  # Will be initialized per session
    
    async def create_session(
        self,
        client_user_id: UUID,
        session_name: Optional[str] = None,
        problem_statement: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new thinking session.
        
        Args:
            client_user_id: ID of the user creating the session
            session_name: Optional name for the session
            problem_statement: Optional problem to solve
            metadata: Optional additional metadata
            
        Returns:
            Created session details
        """
        async with self.async_session() as session:
            try:
                # Initialize validator for this session
                self.schema_validator = ThinkingSchemaValidator(session)
                
                # Validate metadata if provided
                validated_metadata = metadata or {}
                if metadata:
                    validation_result = await self.schema_validator.validate_session_metadata(metadata)
                    if validation_result.valid:
                        validated_metadata.update(validation_result.to_dict())
                    else:
                        logger.warning(f"Session metadata validation failed: {validation_result.errors}")
                        validated_metadata.update(validation_result.to_dict())
                
                # Create new thinking session
                new_session = ThinkingSessions(
                    client_user_id=client_user_id,
                    session_name=session_name,
                    problem_statement=problem_statement,
                    status='active',
                    metadata_json=validated_metadata
                )
                
                session.add(new_session)
                await session.commit()
                await session.refresh(new_session)
                
                logger.info(f"Created thinking session {new_session.id} for user {client_user_id}")
                
                return {
                    "id": str(new_session.id),
                    "client_user_id": str(new_session.client_user_id),
                    "session_name": new_session.session_name,
                    "problem_statement": new_session.problem_statement,
                    "status": new_session.status,
                    "metadata": new_session.metadata_json,
                    "created_at": new_session.created_at.isoformat(),
                    "thoughts": []
                }
                
            except Exception as e:
                logger.error(f"Error creating thinking session: {e}")
                await session.rollback()
                raise
    
    async def add_thought(
        self,
        session_id: UUID,
        thought_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a thought to an active session.
        
        Args:
            session_id: ID of the session
            thought_content: The thought content
            metadata: Optional additional metadata
            
        Returns:
            Created thought details
        """
        async with self.async_session() as session:
            try:
                # Initialize validator for this session
                self.schema_validator = ThinkingSchemaValidator(session)
                
                # Check session exists and is active
                thinking_session = await session.get(ThinkingSessions, session_id)
                if not thinking_session:
                    raise ValueError(f"Session {session_id} not found")
                if thinking_session.status != 'active':
                    raise ValueError(f"Cannot add thoughts to {thinking_session.status} session")
                
                # Get next thought number using database function
                result = await session.execute(
                    text("SELECT get_next_thought_number(:session_id)"),
                    {"session_id": session_id}
                )
                thought_number = result.scalar()
                
                # Validate metadata if provided
                validated_metadata = metadata or {}
                if metadata:
                    validation_result = await self.schema_validator.validate_thought_metadata(metadata, is_revision=False)
                    if validation_result.valid:
                        validated_metadata.update(validation_result.to_dict())
                    else:
                        logger.warning(f"Thought metadata validation failed: {validation_result.errors}")
                        validated_metadata.update(validation_result.to_dict())
                
                # Create new thought
                new_thought = Thoughts(
                    session_id=session_id,
                    thought_number=thought_number,
                    thought_content=thought_content,
                    is_revision=False,
                    metadata_json=validated_metadata
                )
                
                session.add(new_thought)
                await session.commit()
                await session.refresh(new_thought)
                
                logger.info(f"Added thought {thought_number} to session {session_id}")
                
                return {
                    "id": str(new_thought.id),
                    "session_id": str(new_thought.session_id),
                    "thought_number": new_thought.thought_number,
                    "thought_content": new_thought.thought_content,
                    "is_revision": new_thought.is_revision,
                    "metadata": new_thought.metadata_json,
                    "created_at": new_thought.created_at.isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error adding thought: {e}")
                await session.rollback()
                raise
    
    async def revise_thought(
        self,
        session_id: UUID,
        thought_number: int,
        revised_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Revise an existing thought.
        
        Args:
            session_id: ID of the session
            thought_number: Number of thought to revise
            revised_content: The revised content
            metadata: Optional additional metadata
            
        Returns:
            Created revision details
        """
        async with self.async_session() as session:
            try:
                # Initialize validator for this session
                self.schema_validator = ThinkingSchemaValidator(session)
                
                # Check session exists and is active
                thinking_session = await session.get(ThinkingSessions, session_id)
                if not thinking_session:
                    raise ValueError(f"Session {session_id} not found")
                if thinking_session.status != 'active':
                    raise ValueError(f"Cannot revise thoughts in {thinking_session.status} session")
                
                # Check target thought exists
                stmt = select(Thoughts).where(
                    and_(
                        Thoughts.session_id == session_id,
                        Thoughts.thought_number == thought_number
                    )
                )
                result = await session.execute(stmt)
                target_thought = result.scalar_one_or_none()
                
                if not target_thought:
                    raise ValueError(f"Thought {thought_number} not found in session")
                
                # Get next thought number
                result = await session.execute(
                    text("SELECT get_next_thought_number(:session_id)"),
                    {"session_id": session_id}
                )
                next_number = result.scalar()
                
                # Validate metadata if provided
                validated_metadata = metadata or {}
                if metadata:
                    validation_result = await self.schema_validator.validate_thought_metadata(metadata, is_revision=True)
                    if validation_result.valid:
                        validated_metadata.update(validation_result.to_dict())
                    else:
                        logger.warning(f"Revision metadata validation failed: {validation_result.errors}")
                        validated_metadata.update(validation_result.to_dict())
                
                # Create revision
                revision = Thoughts(
                    session_id=session_id,
                    thought_number=next_number,
                    thought_content=revised_content,
                    is_revision=True,
                    revises_thought_number=thought_number,
                    metadata_json=validated_metadata
                )
                
                session.add(revision)
                await session.commit()
                await session.refresh(revision)
                
                logger.info(f"Created revision {next_number} for thought {thought_number} in session {session_id}")
                
                return {
                    "id": str(revision.id),
                    "session_id": str(revision.session_id),
                    "thought_number": revision.thought_number,
                    "thought_content": revision.thought_content,
                    "is_revision": revision.is_revision,
                    "revises_thought_number": revision.revises_thought_number,
                    "metadata": revision.metadata_json,
                    "created_at": revision.created_at.isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error revising thought: {e}")
                await session.rollback()
                raise
    
    async def complete_session(
        self,
        session_id: UUID,
        final_answer: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete a thinking session with final answer.
        
        Args:
            session_id: ID of the session
            final_answer: The final answer/solution
            metadata: Optional additional metadata
            
        Returns:
            Updated session details
        """
        async with self.async_session() as session:
            try:
                # Get session
                thinking_session = await session.get(ThinkingSessions, session_id)
                if not thinking_session:
                    raise ValueError(f"Session {session_id} not found")
                if thinking_session.status != 'active':
                    raise ValueError(f"Session is already {thinking_session.status}")
                
                # Update session
                thinking_session.status = 'completed'
                thinking_session.final_answer = final_answer
                thinking_session.completed_at = datetime.now(timezone.utc)
                
                # Merge metadata
                if metadata:
                    thinking_session.metadata_json = {
                        **thinking_session.metadata_json,
                        **metadata
                    }
                
                await session.commit()
                await session.refresh(thinking_session)
                
                logger.info(f"Completed session {session_id}")
                
                return {
                    "id": str(thinking_session.id),
                    "status": thinking_session.status,
                    "final_answer": thinking_session.final_answer,
                    "completed_at": thinking_session.completed_at.isoformat(),
                    "metadata": thinking_session.metadata_json
                }
                
            except Exception as e:
                logger.error(f"Error completing session: {e}")
                await session.rollback()
                raise
    
    async def abandon_session(
        self,
        session_id: UUID,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Abandon a thinking session.
        
        Args:
            session_id: ID of the session
            reason: Optional reason for abandoning
            metadata: Optional additional metadata
            
        Returns:
            Updated session details
        """
        async with self.async_session() as session:
            try:
                # Get session
                thinking_session = await session.get(ThinkingSessions, session_id)
                if not thinking_session:
                    raise ValueError(f"Session {session_id} not found")
                if thinking_session.status != 'active':
                    raise ValueError(f"Session is already {thinking_session.status}")
                
                # Update session
                thinking_session.status = 'abandoned'
                thinking_session.completed_at = datetime.now(timezone.utc)
                
                # Update metadata with reason
                if reason or metadata:
                    thinking_session.metadata_json = {
                        **thinking_session.metadata_json,
                        **(metadata or {}),
                        "abandon_reason": reason
                    }
                
                await session.commit()
                await session.refresh(thinking_session)
                
                logger.info(f"Abandoned session {session_id}")
                
                return {
                    "id": str(thinking_session.id),
                    "status": thinking_session.status,
                    "completed_at": thinking_session.completed_at.isoformat(),
                    "metadata": thinking_session.metadata_json
                }
                
            except Exception as e:
                logger.error(f"Error abandoning session: {e}")
                await session.rollback()
                raise
    
    async def get_session(
        self,
        session_id: UUID,
        include_thoughts: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get a thinking session by ID.
        
        Args:
            session_id: ID of the session
            include_thoughts: Whether to include thoughts
            
        Returns:
            Session details or None if not found
        """
        async with self.async_session() as session:
            try:
                # Build query
                if include_thoughts:
                    stmt = select(ThinkingSessions).options(
                        selectinload(ThinkingSessions.thoughts)
                    ).where(ThinkingSessions.id == session_id)
                else:
                    stmt = select(ThinkingSessions).where(
                        ThinkingSessions.id == session_id
                    )
                
                result = await session.execute(stmt)
                thinking_session = result.scalar_one_or_none()
                
                if not thinking_session:
                    return None
                
                # Format response
                response = {
                    "id": str(thinking_session.id),
                    "client_user_id": str(thinking_session.client_user_id),
                    "session_name": thinking_session.session_name,
                    "problem_statement": thinking_session.problem_statement,
                    "status": thinking_session.status,
                    "final_answer": thinking_session.final_answer,
                    "metadata": thinking_session.metadata_json,
                    "created_at": thinking_session.created_at.isoformat(),
                    "completed_at": thinking_session.completed_at.isoformat() if thinking_session.completed_at else None
                }
                
                if include_thoughts:
                    response["thoughts"] = [
                        {
                            "id": str(thought.id),
                            "thought_number": thought.thought_number,
                            "thought_content": thought.thought_content,
                            "is_revision": thought.is_revision,
                            "revises_thought_number": thought.revises_thought_number,
                            "metadata": thought.metadata_json,
                            "created_at": thought.created_at.isoformat()
                        }
                        for thought in sorted(thinking_session.thoughts, key=lambda t: t.thought_number)
                    ]
                
                return response
                
            except Exception as e:
                logger.error(f"Error getting session: {e}")
                raise
    
    async def list_sessions(
        self,
        client_user_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        List thinking sessions for a user.
        
        Args:
            client_user_id: User ID to filter by
            status: Optional status filter
            page: Page number (1-based)
            page_size: Items per page
            
        Returns:
            Paginated list of sessions
        """
        async with self.async_session() as session:
            try:
                # Build base query
                stmt = select(ThinkingSessions).where(
                    ThinkingSessions.client_user_id == client_user_id
                )
                
                if status:
                    stmt = stmt.where(ThinkingSessions.status == status)
                
                # Get total count
                count_stmt = select(func.count()).select_from(stmt.subquery())
                result = await session.execute(count_stmt)
                total = result.scalar()
                
                # Apply pagination
                offset = (page - 1) * page_size
                stmt = stmt.order_by(ThinkingSessions.created_at.desc())
                stmt = stmt.offset(offset).limit(page_size)
                
                # Execute query
                result = await session.execute(stmt)
                sessions = result.scalars().all()
                
                # Format response
                return {
                    "sessions": [
                        {
                            "id": str(s.id),
                            "client_user_id": str(s.client_user_id),
                            "session_name": s.session_name,
                            "problem_statement": s.problem_statement,
                            "status": s.status,
                            "final_answer": s.final_answer,
                            "metadata": s.metadata_json,
                            "created_at": s.created_at.isoformat(),
                            "completed_at": s.completed_at.isoformat() if s.completed_at else None
                        }
                        for s in sessions
                    ],
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
                
            except Exception as e:
                logger.error(f"Error listing sessions: {e}")
                raise
    
    async def get_session_stats(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a thinking session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session statistics or None if not found
        """
        async with self.async_session() as session:
            try:
                # Query the stats view
                stmt = text("""
                    SELECT 
                        session_id,
                        client_user_id,
                        status,
                        total_thoughts,
                        revision_count,
                        revised_thought_numbers,
                        average_thought_length,
                        duration_seconds,
                        thoughts_per_minute
                    FROM thinking_session_stats
                    WHERE session_id = :session_id
                """)
                
                result = await session.execute(stmt, {"session_id": session_id})
                row = result.fetchone()
                
                if not row:
                    return None
                
                return {
                    "session_id": str(row.session_id),
                    "client_user_id": str(row.client_user_id),
                    "status": row.status,
                    "total_thoughts": row.total_thoughts,
                    "revision_count": row.revision_count,
                    "revised_thought_numbers": row.revised_thought_numbers or [],
                    "average_thought_length": row.average_thought_length,
                    "duration_seconds": row.duration_seconds,
                    "thoughts_per_minute": round(row.thoughts_per_minute, 2) if row.thoughts_per_minute else 0
                }
                
            except Exception as e:
                logger.error(f"Error getting session stats: {e}")
                raise