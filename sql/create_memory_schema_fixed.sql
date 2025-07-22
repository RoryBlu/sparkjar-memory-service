-- Memory Service Complete Schema (Fixed for Python execution)
-- This script creates all tables needed for the memory and thinking services
-- It will DROP existing tables and recreate them

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Drop existing tables if they exist
DROP TABLE IF EXISTS thoughts CASCADE;
DROP TABLE IF EXISTS thinking_sessions CASCADE;
DROP TABLE IF EXISTS memory_observations CASCADE;
DROP TABLE IF EXISTS memory_relations CASCADE;
DROP TABLE IF EXISTS memory_entities CASCADE;

-- Create memory_entities table
CREATE TABLE memory_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    actor_type VARCHAR(50) NOT NULL CHECK (actor_type IN ('human', 'synth', 'system')),
    actor_id UUID NOT NULL,
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(768),
    identity_confidence NUMERIC(3,2) NOT NULL DEFAULT 1.00,
    alias_of UUID NULL REFERENCES memory_entities(id),
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_entity_name_per_client UNIQUE (client_id, entity_name, deleted_at)
);

-- Create memory_observations table
CREATE TABLE memory_observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL REFERENCES memory_entities(id) ON DELETE CASCADE,
    observation_type VARCHAR(50) NOT NULL,
    observation_value JSONB NOT NULL,
    source VARCHAR(100) DEFAULT 'api',
    confidence FLOAT DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1),
    tags TEXT[] DEFAULT '{}',
    context JSONB DEFAULT '{}',
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    skill_name VARCHAR(255) GENERATED ALWAYS AS (observation_value->>'skill_name') STORED,
    skill_category VARCHAR(50) GENERATED ALWAYS AS (observation_value->>'skill_category') STORED,
    proficiency_level VARCHAR(50) GENERATED ALWAYS AS (observation_value->>'proficiency_level') STORED
);

-- Create memory_relations table
CREATE TABLE memory_relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    actor_type VARCHAR(50) NOT NULL CHECK (actor_type IN ('human', 'synth', 'system')),
    actor_id UUID NOT NULL,
    from_entity_id UUID NOT NULL REFERENCES memory_entities(id) ON DELETE CASCADE,
    to_entity_id UUID NOT NULL REFERENCES memory_entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_relation UNIQUE (from_entity_id, to_entity_id, relation_type, deleted_at),
    CONSTRAINT no_self_relation CHECK (from_entity_id != to_entity_id)
);

-- Create thinking_sessions table
CREATE TABLE thinking_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_user_id UUID NOT NULL,
    session_name TEXT,
    problem_statement TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned')),
    final_answer TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT final_answer_required_when_completed CHECK (
        (status = 'completed' AND final_answer IS NOT NULL) OR 
        (status != 'completed')
    ),
    CONSTRAINT completed_at_required_when_not_active CHECK (
        (status = 'active' AND completed_at IS NULL) OR
        (status != 'active' AND completed_at IS NOT NULL)
    )
);

-- Create thoughts table
CREATE TABLE thoughts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES thinking_sessions(id) ON DELETE CASCADE,
    thought_number INTEGER NOT NULL CHECK (thought_number > 0),
    thought_content TEXT NOT NULL CHECK (length(thought_content) >= 1 AND length(thought_content) <= 10000),
    is_revision BOOLEAN NOT NULL DEFAULT false,
    revises_thought_number INTEGER,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_thought_number_per_session UNIQUE (session_id, thought_number),
    CONSTRAINT revision_requires_target CHECK (
        (is_revision = true AND revises_thought_number IS NOT NULL) OR
        (is_revision = false AND revises_thought_number IS NULL)
    ),
    CONSTRAINT revision_must_be_earlier CHECK (
        revises_thought_number IS NULL OR revises_thought_number < thought_number
    )
);

-- Create indexes for memory_entities
CREATE INDEX idx_memory_entities_client_id ON memory_entities(client_id);
CREATE INDEX idx_memory_entities_actor ON memory_entities(actor_type, actor_id);
CREATE INDEX idx_memory_entities_type ON memory_entities(entity_type);
CREATE INDEX idx_memory_entities_name ON memory_entities(entity_name);
CREATE INDEX idx_memory_entities_deleted ON memory_entities(deleted_at);
CREATE INDEX idx_memory_entities_embedding ON memory_entities USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_memory_entities_alias_of ON memory_entities(alias_of);

-- Create indexes for memory_observations
CREATE INDEX idx_memory_observations_entity ON memory_observations(entity_id);
CREATE INDEX idx_memory_observations_type ON memory_observations(observation_type);
CREATE INDEX idx_memory_observations_created ON memory_observations(created_at DESC);
CREATE INDEX idx_memory_observations_skill_name ON memory_observations(skill_name) WHERE skill_name IS NOT NULL;
CREATE INDEX idx_memory_observations_skill_category ON memory_observations(skill_category) WHERE skill_category IS NOT NULL;
CREATE INDEX idx_memory_observations_tags ON memory_observations USING gin(tags);

-- Create indexes for memory_relations
CREATE INDEX idx_memory_relations_client ON memory_relations(client_id);
CREATE INDEX idx_memory_relations_from ON memory_relations(from_entity_id);
CREATE INDEX idx_memory_relations_to ON memory_relations(to_entity_id);
CREATE INDEX idx_memory_relations_type ON memory_relations(relation_type);
CREATE INDEX idx_memory_relations_deleted ON memory_relations(deleted_at);

-- Create indexes for thinking_sessions
CREATE INDEX idx_thinking_sessions_client_user_id ON thinking_sessions(client_user_id);
CREATE INDEX idx_thinking_sessions_status ON thinking_sessions(status);
CREATE INDEX idx_thinking_sessions_created_at ON thinking_sessions(created_at DESC);
CREATE INDEX idx_thinking_sessions_client_status_created ON thinking_sessions(client_user_id, status, created_at DESC);

-- Create indexes for thoughts
CREATE INDEX idx_thoughts_session_id ON thoughts(session_id);
CREATE INDEX idx_thoughts_session_thought_number ON thoughts(session_id, thought_number);
CREATE INDEX idx_thoughts_revises ON thoughts(session_id, revises_thought_number) WHERE revises_thought_number IS NOT NULL;

-- Grant permissions (for system access, no user RLS)
GRANT ALL ON memory_entities TO service_role;
GRANT ALL ON memory_observations TO service_role;
GRANT ALL ON memory_relations TO service_role;
GRANT ALL ON thinking_sessions TO service_role;
GRANT ALL ON thoughts TO service_role;

-- Add comments for documentation
COMMENT ON TABLE memory_entities IS 'Core entities in the memory system (people, projects, skills, etc)';
COMMENT ON TABLE memory_observations IS 'Individual observations about entities with support for embeddings';
COMMENT ON TABLE memory_relations IS 'Relationships between entities in the knowledge graph';
COMMENT ON TABLE thinking_sessions IS 'Sequential thinking problem-solving sessions';
COMMENT ON TABLE thoughts IS 'Individual thoughts within a thinking session';

COMMENT ON COLUMN memory_entities.embedding IS 'Vector embedding using Alibaba-NLP/gte-multilingual-base (768 dimensions)';
COMMENT ON COLUMN memory_observations.embedding IS 'Optional embedding for observation-level semantic search';
COMMENT ON COLUMN memory_observations.observation_value IS 'JSONB containing the observation data based on type';