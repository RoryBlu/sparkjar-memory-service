from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID

class CreateSessionRequest(BaseModel):
    client_user_id: UUID
    session_name: Optional[str] = None
    problem_statement: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AddThoughtRequest(BaseModel):
    session_id: UUID
    thought_content: str
    metadata: Optional[Dict[str, Any]] = None

class ReviseThoughtRequest(BaseModel):
    session_id: UUID
    thought_number: int
    revised_content: str
    metadata: Optional[Dict[str, Any]] = None

class CompleteSessionRequest(BaseModel):
    session_id: UUID
    final_answer: str
    metadata: Optional[Dict[str, Any]] = None

class AbandonSessionRequest(BaseModel):
    session_id: UUID
    reason: str
    metadata: Optional[Dict[str, Any]] = None
