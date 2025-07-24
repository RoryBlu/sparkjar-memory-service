-- Create skill_module table for Memory Maker Crew Production Ready feature
-- This table stores skill module definitions that can be used as memory contexts

-- Create skill_modules table
CREATE TABLE IF NOT EXISTS skill_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50),
    active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT skill_modules_name_version_unique UNIQUE (name, version)
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_skill_modules_name ON skill_modules(name);
CREATE INDEX IF NOT EXISTS idx_skill_modules_active ON skill_modules(active);
CREATE INDEX IF NOT EXISTS idx_skill_modules_created_at ON skill_modules(created_at);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_skill_modules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER skill_modules_updated_at_trigger
    BEFORE UPDATE ON skill_modules
    FOR EACH ROW
    EXECUTE FUNCTION update_skill_modules_updated_at();

-- Add comment to document the table
COMMENT ON TABLE skill_modules IS 'Stores skill module definitions that provide specialized knowledge and procedures for agents';
COMMENT ON COLUMN skill_modules.id IS 'Unique identifier for the skill module';
COMMENT ON COLUMN skill_modules.name IS 'Human-readable name of the skill module';
COMMENT ON COLUMN skill_modules.description IS 'Detailed description of what the skill module provides';
COMMENT ON COLUMN skill_modules.version IS 'Version identifier for the skill module';
COMMENT ON COLUMN skill_modules.active IS 'Whether this skill module is currently active and available';
COMMENT ON COLUMN skill_modules.metadata IS 'Additional metadata about the skill module (JSON)';

-- Insert sample skill modules for testing
INSERT INTO skill_modules (name, description, version, metadata) VALUES
    (
        'content_analysis',
        'Skill module for analyzing and extracting insights from various content types',
        '1.0.0',
        '{
            "capabilities": ["text_analysis", "entity_extraction", "sentiment_analysis"],
            "supported_formats": ["text", "markdown", "html"],
            "performance_metrics": {
                "accuracy": 0.92,
                "processing_speed": "fast"
            }
        }'::jsonb
    ),
    (
        'memory_structuring',
        'Skill module for organizing and structuring memories into hierarchical knowledge',
        '1.0.0',
        '{
            "capabilities": ["memory_organization", "relationship_mapping", "context_preservation"],
            "memory_types": ["procedural", "declarative", "episodic"],
            "hierarchy_support": true
        }'::jsonb
    ),
    (
        'policy_interpretation',
        'Skill module specialized in understanding and extracting rules from policy documents',
        '1.0.0',
        '{
            "capabilities": ["policy_parsing", "rule_extraction", "compliance_mapping"],
            "document_types": ["corporate_policy", "legal_document", "regulatory_text"],
            "extraction_confidence": 0.95
        }'::jsonb
    )
ON CONFLICT (name, version) DO NOTHING;

-- Update object_schemas to support skill_module actor type
UPDATE object_schemas 
SET schema = jsonb_set(
    schema,
    '{properties,actor_type,enum}',
    '["synth", "human", "client", "synth_class", "skill_module"]'::jsonb
),
updated_at = NOW()
WHERE name = 'memory_maker_crew' AND object_type = 'crew';

-- Also update the base_observation schema to support skill_module
UPDATE object_schemas 
SET schema = jsonb_set(
    schema,
    '{properties,actor_type,enum}',
    '["synth", "human", "client", "synth_class", "skill_module"]'::jsonb
),
updated_at = NOW()
WHERE name = 'base_observation' AND object_type = 'observation';

-- Grant appropriate permissions (adjust based on your user setup)
-- GRANT SELECT, INSERT, UPDATE ON skill_modules TO your_app_user;
-- GRANT USAGE ON SEQUENCE skill_modules_id_seq TO your_app_user;