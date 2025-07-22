-- Migration: Add actor_id validation to memory system
-- This migration adds database-level validation to ensure actor_id references
-- exist in the appropriate tables based on actor_type

-- Create validation function
CREATE OR REPLACE FUNCTION validate_actor_reference()
RETURNS TRIGGER AS $$
DECLARE
    table_name TEXT;
    query TEXT;
    result BOOLEAN;
BEGIN
    -- Map actor_type to table
    CASE NEW.actor_type
        WHEN 'human' THEN table_name := 'client_users';
        WHEN 'synth' THEN table_name := 'synths';
        WHEN 'synth_class' THEN table_name := 'synth_classes';
        WHEN 'client' THEN table_name := 'clients';
        ELSE RAISE EXCEPTION 'Invalid actor_type: %', NEW.actor_type;
    END CASE;
    
    -- Check if actor_id exists in corresponding table
    query := format('SELECT EXISTS(SELECT 1 FROM %I WHERE id = $1)', table_name);
    EXECUTE query INTO result USING NEW.actor_id;
    
    IF NOT result THEN
        RAISE EXCEPTION 'Actor % of type % does not exist in table %', 
            NEW.actor_id, NEW.actor_type, table_name;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger to memory_entities
CREATE TRIGGER validate_actor_ref_entities
BEFORE INSERT OR UPDATE OF actor_id, actor_type ON memory_entities
FOR EACH ROW EXECUTE FUNCTION validate_actor_reference();

-- Create metrics table for monitoring validation performance
CREATE TABLE IF NOT EXISTS actor_validation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_type VARCHAR(50) NOT NULL,
    actor_id UUID NOT NULL,
    validation_result BOOLEAN NOT NULL,
    validation_time_ms FLOAT NOT NULL,
    cache_hit BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance monitoring
CREATE INDEX IF NOT EXISTS idx_validation_metrics_created 
ON actor_validation_metrics(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_validation_metrics_result 
ON actor_validation_metrics(actor_type, validation_result);

-- Create index on validation metrics for cleanup
CREATE INDEX IF NOT EXISTS idx_validation_metrics_cleanup 
ON actor_validation_metrics(created_at) 
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '7 days';

-- Add comment to explain the trigger
COMMENT ON FUNCTION validate_actor_reference() IS 
'Validates that actor_id exists in the appropriate table based on actor_type. 
Maps: human->client_users, synth->synths, synth_class->synth_classes, client->clients';

COMMENT ON TRIGGER validate_actor_ref_entities ON memory_entities IS 
'Ensures referential integrity for actor_id based on actor_type';