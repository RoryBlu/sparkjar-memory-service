-- Functions and Views for Memory Service
-- Run this after creating the main tables

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_memory_entities_updated_at BEFORE UPDATE ON memory_entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memory_relations_updated_at BEFORE UPDATE ON memory_relations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Helper function to get next thought number
CREATE OR REPLACE FUNCTION get_next_thought_number(p_session_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_next_number INTEGER;
    v_session_status TEXT;
BEGIN
    -- Check session status
    SELECT status INTO v_session_status
    FROM thinking_sessions
    WHERE id = p_session_id;
    
    IF v_session_status != 'active' THEN
        RAISE EXCEPTION 'Cannot add thoughts to % session', v_session_status;
    END IF;
    
    -- Get next number
    SELECT COALESCE(MAX(thought_number), 0) + 1 INTO v_next_number
    FROM thoughts
    WHERE session_id = p_session_id;
    
    RETURN v_next_number;
END;
$$ LANGUAGE plpgsql;

-- Create view for session statistics
CREATE OR REPLACE VIEW thinking_session_stats AS
SELECT 
    ts.id as session_id,
    ts.client_user_id,
    ts.status,
    COUNT(t.id) as total_thoughts,
    COUNT(t.id) FILTER (WHERE t.is_revision = true) as revision_count,
    ARRAY_AGG(DISTINCT t.revises_thought_number ORDER BY t.revises_thought_number) 
        FILTER (WHERE t.revises_thought_number IS NOT NULL) as revised_thought_numbers,
    AVG(length(t.thought_content))::INTEGER as average_thought_length,
    EXTRACT(EPOCH FROM (COALESCE(ts.completed_at, NOW()) - ts.created_at))::INTEGER as duration_seconds,
    CASE 
        WHEN EXTRACT(EPOCH FROM (COALESCE(ts.completed_at, NOW()) - ts.created_at)) > 0 
        THEN COUNT(t.id)::FLOAT / (EXTRACT(EPOCH FROM (COALESCE(ts.completed_at, NOW()) - ts.created_at)) / 60)
        ELSE 0 
    END as thoughts_per_minute
FROM thinking_sessions ts
LEFT JOIN thoughts t ON ts.id = t.session_id
GROUP BY ts.id, ts.client_user_id, ts.status, ts.created_at, ts.completed_at;

-- Grant permissions for functions and views
GRANT SELECT ON thinking_session_stats TO service_role;
GRANT EXECUTE ON FUNCTION get_next_thought_number(UUID) TO service_role;
GRANT EXECUTE ON FUNCTION update_updated_at_column() TO service_role;