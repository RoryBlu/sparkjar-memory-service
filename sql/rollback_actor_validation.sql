-- Rollback: Remove actor_id validation from memory system
-- This script removes the validation trigger and related objects

-- Drop triggers
DROP TRIGGER IF EXISTS validate_actor_ref_entities ON memory_entities;

-- Drop validation function
DROP FUNCTION IF EXISTS validate_actor_reference();

-- Drop metrics table and its indexes
DROP TABLE IF EXISTS actor_validation_metrics CASCADE;

-- Note: This rollback does not remove any data, only the validation mechanism