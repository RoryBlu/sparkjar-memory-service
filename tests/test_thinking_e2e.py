"""
End-to-end tests for sequential thinking service.
Tests complete thinking workflows with real database operations.
"""
import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
import json

# Test user
TEST_USER_ID = uuid4()

@pytest.mark.asyncio
async def test_complete_thinking_session_workflow(thinking_service):
    """Test complete thinking session lifecycle"""
    
    # Step 1: Create a thinking session with metadata
    session_metadata = {
        "context": {
            "domain": "system_design",
            "task_type": "problem_solving",
            "complexity": "complex"
        },
        "goals": [
            "Design a scalable microservices architecture",
            "Ensure fault tolerance",
            "Optimize for performance"
        ],
        "constraints": [
            "Must handle 10k requests/second",
            "99.9% uptime requirement",
            "Budget limit of $50k/month"
        ],
        "participants": [
            {"name": "Alice Johnson", "role": "architect"},
            {"name": "AI Assistant", "role": "advisor"}
        ]
    }
    
    session = await thinking_service.create_session(
        client_user_id=TEST_USER_ID,
        session_name="Microservices Architecture Design",
        problem_statement="Design a scalable e-commerce platform that can handle Black Friday traffic",
        metadata=session_metadata
    )
    
    assert session["id"]
    assert session["status"] == "active"
    assert session["metadata"]["_schema_used"] == "thinking_session_metadata"
    assert session["metadata"]["_validation_passed"] == True
    session_id = uuid4.UUID(session["id"])
    
    # Step 2: Add initial thoughts
    thoughts = [
        {
            "content": "We need to identify the core services: user management, product catalog, cart, payment, and order processing.",
            "metadata": {
                "thought_type": "observation",
                "confidence": 0.9,
                "reasoning_method": "deductive",
                "tags": ["architecture", "services"]
            }
        },
        {
            "content": "Each service should have its own database to ensure true decoupling and independent scaling.",
            "metadata": {
                "thought_type": "hypothesis",
                "confidence": 0.85,
                "reasoning_method": "inductive",
                "evidence": [
                    {"source": "microservices_best_practices", "strength": "strong"},
                    {"source": "past_experience", "strength": "moderate"}
                ]
            }
        },
        {
            "content": "How do we handle distributed transactions across services?",
            "metadata": {
                "thought_type": "question",
                "next_steps": ["Research saga pattern", "Evaluate 2PC alternatives"]
            }
        }
    ]
    
    created_thoughts = []
    for thought in thoughts:
        result = await thinking_service.add_thought(
            session_id=session_id,
            thought_content=thought["content"],
            metadata=thought["metadata"]
        )
        created_thoughts.append(result)
        
        # Verify thought was created with validation
        assert result["thought_number"] > 0
        assert result["metadata"]["_schema_used"] == "thought_metadata"
        assert result["metadata"]["_validation_passed"] == True
    
    # Step 3: Revise a thought
    revision_metadata = {
        "revision_type": "expansion",
        "revision_reason": "Need to provide specific database recommendations",
        "changes_made": [
            {
                "aspect": "database_details",
                "from": "own database",
                "to": "PostgreSQL for transactional data, MongoDB for product catalog",
                "rationale": "Different data patterns require different storage solutions"
            }
        ],
        "impact_assessment": {
            "clarity_improvement": "significant",
            "accuracy_improvement": "moderate",
            "completeness_improvement": "major"
        }
    }
    
    revision = await thinking_service.revise_thought(
        session_id=session_id,
        thought_number=2,  # Revise the database thought
        revised_content="Each service should use the appropriate database: PostgreSQL for transactional services (users, orders), MongoDB for product catalog, Redis for cart sessions.",
        metadata=revision_metadata
    )
    
    assert revision["is_revision"] == True
    assert revision["revises_thought_number"] == 2
    assert revision["metadata"]["_schema_used"] == "revision_metadata"
    
    # Step 4: Add more thoughts building on previous ones
    followup_thoughts = [
        {
            "content": "Implement the Saga pattern using an orchestrator service to manage distributed transactions.",
            "metadata": {
                "thought_type": "answer",
                "confidence": 0.8,
                "reasoning_method": "analogical",
                "evidence": [
                    {"source": "saga_pattern_paper", "reference": "Garcia-Molina & Salem, 1987", "strength": "strong"}
                ],
                "alternatives_considered": [
                    {"alternative": "2PC (Two-Phase Commit)", "reason_rejected": "Too much latency and coupling"},
                    {"alternative": "Event sourcing only", "reason_rejected": "Too complex for all services"}
                ]
            }
        },
        {
            "content": "Use API Gateway pattern with Kong or AWS API Gateway for request routing, rate limiting, and authentication.",
            "metadata": {
                "thought_type": "action",
                "confidence": 0.95,
                "reasoning_method": "deductive",
                "next_steps": [
                    "Evaluate Kong vs AWS API Gateway",
                    "Design authentication flow",
                    "Plan rate limiting strategy"
                ]
            }
        }
    ]
    
    for thought in followup_thoughts:
        await thinking_service.add_thought(
            session_id=session_id,
            thought_content=thought["content"],
            metadata=thought["metadata"]
        )
    
    # Step 5: Get current session state
    current_session = await thinking_service.get_session(session_id)
    
    assert len(current_session["thoughts"]) >= 6  # Original + revision + followups
    assert current_session["status"] == "active"
    
    # Verify thought ordering
    thought_numbers = [t["thought_number"] for t in current_session["thoughts"]]
    assert thought_numbers == sorted(thought_numbers)  # Should be in order
    
    # Step 6: Complete the session with final answer
    final_answer = """
    Microservices Architecture Design:
    
    1. Core Services: User, Product, Cart, Payment, Order
    2. Databases: PostgreSQL (transactional), MongoDB (catalog), Redis (sessions)
    3. Communication: REST + async messaging (RabbitMQ)
    4. Transactions: Saga pattern with orchestrator
    5. API Gateway: Kong for routing and rate limiting
    6. Deployment: Kubernetes with auto-scaling
    7. Monitoring: Prometheus + Grafana + ELK stack
    """
    
    completed = await thinking_service.complete_session(
        session_id=session_id,
        final_answer=final_answer
    )
    
    assert completed["status"] == "completed"
    assert completed["final_answer"] == final_answer
    assert completed["completed_at"]

@pytest.mark.asyncio
async def test_complex_revision_chain(thinking_service):
    """Test complex chains of thought revisions"""
    
    # Create session
    session = await thinking_service.create_session(
        client_user_id=TEST_USER_ID,
        session_name="Revision Chain Test",
        problem_statement="Test multiple revisions"
    )
    session_id = uuid4.UUID(session["id"])
    
    # Add initial thought
    thought1 = await thinking_service.add_thought(
        session_id=session_id,
        thought_content="Initial hypothesis about the problem",
        metadata={"thought_type": "hypothesis", "confidence": 0.5}
    )
    
    # First revision
    revision1 = await thinking_service.revise_thought(
        session_id=session_id,
        thought_number=thought1["thought_number"],
        revised_content="Refined hypothesis with more detail",
        metadata={
            "revision_type": "refinement",
            "revision_reason": "Initial hypothesis was too vague"
        }
    )
    
    # Second revision of the same thought
    revision2 = await thinking_service.revise_thought(
        session_id=session_id,
        thought_number=thought1["thought_number"],
        revised_content="Final hypothesis with concrete predictions",
        metadata={
            "revision_type": "complete_rethink",
            "revision_reason": "New evidence changed perspective",
            "lessons_learned": ["Need to consider edge cases", "Initial assumptions were flawed"]
        }
    )
    
    # Get revision history
    history = await thinking_service.get_thought_history(
        session_id=session_id,
        thought_number=thought1["thought_number"]
    )
    
    assert len(history) == 3  # Original + 2 revisions
    assert history[0]["is_revision"] == False
    assert history[1]["is_revision"] == True
    assert history[2]["is_revision"] == True
    
    # Verify revision metadata
    assert history[2]["metadata"]["revision_type"] == "complete_rethink"

@pytest.mark.asyncio
async def test_parallel_thinking_sessions(thinking_service):
    """Test multiple concurrent thinking sessions"""
    
    # Create multiple sessions concurrently
    session_tasks = []
    for i in range(5):
        task = thinking_service.create_session(
            client_user_id=TEST_USER_ID,
            session_name=f"Parallel Session {i}",
            problem_statement=f"Problem {i}",
            metadata={
                "context": {
                    "task_type": "analysis",
                    "complexity": "moderate"
                },
                "goals": [f"Goal {i}"]
            }
        )
        session_tasks.append(task)
    
    sessions = await asyncio.gather(*session_tasks)
    assert len(sessions) == 5
    
    # Add thoughts to each session concurrently
    thought_tasks = []
    for session in sessions:
        session_id = uuid4.UUID(session["id"])
        for j in range(3):
            task = thinking_service.add_thought(
                session_id=session_id,
                thought_content=f"Thought {j} for session {session['session_name']}",
                metadata={"thought_type": "observation"}
            )
            thought_tasks.append(task)
    
    thoughts = await asyncio.gather(*thought_tasks)
    assert len(thoughts) == 15  # 5 sessions × 3 thoughts
    
    # Verify all sessions have correct thoughts
    for session in sessions:
        session_data = await thinking_service.get_session(uuid4.UUID(session["id"]))
        assert len(session_data["thoughts"]) == 3

@pytest.mark.asyncio
async def test_thinking_patterns_extraction(thinking_service):
    """Test extraction and analysis of thinking patterns"""
    
    # Create session focused on pattern detection
    session = await thinking_service.create_session(
        client_user_id=TEST_USER_ID,
        session_name="Pattern Analysis Session",
        metadata={
            "context": {"task_type": "analysis"},
            "goals": ["Identify thinking patterns"]
        }
    )
    session_id = uuid4.UUID(session["id"])
    
    # Add thoughts that demonstrate patterns
    pattern_thoughts = [
        # Pattern: Always starting with questions
        {"content": "What are the key requirements?", "type": "question"},
        {"content": "Initial analysis of requirements", "type": "observation"},
        
        {"content": "What are the main constraints?", "type": "question"},
        {"content": "Constraint analysis", "type": "observation"},
        
        {"content": "What are the risks?", "type": "question"},
        {"content": "Risk assessment", "type": "observation"},
        
        # Pattern: Revision after reflection
        {"content": "Solution A seems best", "type": "hypothesis", "confidence": 0.7},
        {"content": "Actually, I need to reconsider", "type": "reflection"},
        {"content": "Solution B is better", "type": "hypothesis", "confidence": 0.9}
    ]
    
    for i, thought in enumerate(pattern_thoughts):
        metadata = {"thought_type": thought["type"]}
        if "confidence" in thought:
            metadata["confidence"] = thought["confidence"]
            
        await thinking_service.add_thought(
            session_id=session_id,
            thought_content=thought["content"],
            metadata=metadata
        )
    
    # Analyze patterns (this would be done by a separate analysis function)
    session_data = await thinking_service.get_session(session_id)
    thoughts = session_data["thoughts"]
    
    # Identify question-first pattern
    question_indices = [i for i, t in enumerate(thoughts) 
                       if t["metadata"].get("thought_type") == "question"]
    
    # Verify pattern: questions followed by observations
    for idx in question_indices[:-1]:  # Exclude last if it's the final thought
        next_thought = thoughts[idx + 1]
        assert next_thought["metadata"].get("thought_type") in ["observation", "answer"]

@pytest.mark.asyncio
async def test_session_context_persistence(thinking_service):
    """Test that session context and metadata persist correctly"""
    
    # Create session with rich metadata
    rich_metadata = {
        "context": {
            "domain": "healthcare",
            "task_type": "decision_making",
            "complexity": "very_complex",
            "time_constraint": "P1D"  # 1 day
        },
        "participants": [
            {"name": "Dr. Smith", "role": "physician", "entity_id": str(uuid4())},
            {"name": "AI Medical Assistant", "role": "advisor"}
        ],
        "resources": [
            {"type": "research_paper", "reference": "PMC123456", "description": "Recent study on treatment"},
            {"type": "guideline", "reference": "WHO-2024-01", "description": "WHO treatment guidelines"}
        ],
        "constraints": [
            "Patient has allergies to common medications",
            "Limited to FDA-approved treatments",
            "Cost must be under insurance coverage"
        ]
    }
    
    session = await thinking_service.create_session(
        client_user_id=TEST_USER_ID,
        session_name="Medical Decision Support",
        problem_statement="Determine best treatment plan for patient with complex conditions",
        metadata=rich_metadata
    )
    
    # Retrieve session and verify all metadata persists
    retrieved = await thinking_service.get_session(uuid4.UUID(session["id"]))
    
    assert retrieved["metadata"]["context"]["domain"] == "healthcare"
    assert len(retrieved["metadata"]["participants"]) == 2
    assert len(retrieved["metadata"]["resources"]) == 2
    assert retrieved["metadata"]["participants"][0]["entity_id"]  # UUID preserved

@pytest.mark.asyncio
async def test_abandoned_session_handling(thinking_service):
    """Test handling of abandoned/incomplete sessions"""
    
    # Create sessions with different states
    active_session = await thinking_service.create_session(
        client_user_id=TEST_USER_ID,
        session_name="Active Session"
    )
    
    # Add some thoughts
    await thinking_service.add_thought(
        session_id=uuid4.UUID(active_session["id"]),
        thought_content="Working on this...",
        metadata={"thought_type": "observation"}
    )
    
    # Create another session that will be abandoned
    abandoned_session = await thinking_service.create_session(
        client_user_id=TEST_USER_ID,
        session_name="Abandoned Session"
    )
    
    # Get active sessions for user
    active_sessions = await thinking_service.get_active_sessions(TEST_USER_ID)
    
    assert len(active_sessions) >= 2
    session_names = [s["session_name"] for s in active_sessions]
    assert "Active Session" in session_names
    assert "Abandoned Session" in session_names
    
    # Complete one session
    await thinking_service.complete_session(
        session_id=uuid4.UUID(active_session["id"]),
        final_answer="Problem solved"
    )
    
    # Now only abandoned session should be active
    active_sessions = await thinking_service.get_active_sessions(TEST_USER_ID)
    active_names = [s["session_name"] for s in active_sessions]
    assert "Active Session" not in active_names
    assert "Abandoned Session" in active_names

@pytest.mark.asyncio
async def test_thought_metadata_evolution(thinking_service):
    """Test how thought metadata evolves through a session"""
    
    session = await thinking_service.create_session(
        client_user_id=TEST_USER_ID,
        session_name="Metadata Evolution Test"
    )
    session_id = uuid4.UUID(session["id"])
    
    # Early thought - low confidence, few assumptions
    early_thought = await thinking_service.add_thought(
        session_id=session_id,
        thought_content="Initial hypothesis based on limited information",
        metadata={
            "thought_type": "hypothesis",
            "confidence": 0.3,
            "assumptions": ["Data is representative", "No hidden variables"],
            "evidence": []
        }
    )
    
    # Middle thought - gathering evidence
    middle_thought = await thinking_service.add_thought(
        session_id=session_id,
        thought_content="Found supporting evidence in the data",
        metadata={
            "thought_type": "observation",
            "confidence": 0.6,
            "evidence": [
                {"source": "data_analysis", "reference": "Table 3", "strength": "moderate"},
                {"source": "literature", "reference": "Smith et al. 2023", "strength": "strong"}
            ]
        }
    )
    
    # Later thought - high confidence conclusion
    final_thought = await thinking_service.add_thought(
        session_id=session_id,
        thought_content="Conclusion: The hypothesis is supported with modifications",
        metadata={
            "thought_type": "conclusion",
            "confidence": 0.85,
            "reasoning_method": "inductive",
            "evidence": [
                {"source": "data_analysis", "strength": "strong"},
                {"source": "literature", "strength": "strong"},
                {"source": "expert_consultation", "strength": "moderate"}
            ],
            "alternatives_considered": [
                {"alternative": "Null hypothesis", "reason_rejected": "Data shows clear pattern"},
                {"alternative": "Alternative explanation X", "reason_rejected": "Doesn't account for Y"}
            ]
        }
    )
    
    # Analyze confidence progression
    session_data = await thinking_service.get_session(session_id)
    confidences = [
        t["metadata"].get("confidence", 0) 
        for t in session_data["thoughts"]
        if "confidence" in t["metadata"]
    ]
    
    # Confidence should generally increase
    assert confidences[-1] > confidences[0]
    
    # Evidence should accumulate
    evidence_counts = [
        len(t["metadata"].get("evidence", []))
        for t in session_data["thoughts"]
    ]
    assert evidence_counts[-1] > evidence_counts[0]

@pytest.mark.asyncio
async def test_error_recovery_in_thinking(thinking_service):
    """Test error handling and recovery in thinking operations"""
    
    # Test invalid session operations
    fake_session_id = uuid4()
    
    with pytest.raises(ValueError, match="not found"):
        await thinking_service.add_thought(
            session_id=fake_session_id,
            thought_content="This should fail"
        )
    
    # Create valid session
    session = await thinking_service.create_session(
        client_user_id=TEST_USER_ID,
        session_name="Error Recovery Test"
    )
    session_id = uuid4.UUID(session["id"])
    
    # Complete the session
    await thinking_service.complete_session(
        session_id=session_id,
        final_answer="Done"
    )
    
    # Try to add thought to completed session
    with pytest.raises(ValueError, match="Cannot add thoughts"):
        await thinking_service.add_thought(
            session_id=session_id,
            thought_content="This should also fail"
        )
    
    # Verify we can still create new sessions after errors
    new_session = await thinking_service.create_session(
        client_user_id=TEST_USER_ID,
        session_name="Post-Error Session"
    )
    assert new_session["status"] == "active"