-- Fix memory_observations table to follow KISS principles
-- Remove unnecessary columns that violate simplicity

-- First, drop the generated columns
ALTER TABLE memory_observations 
DROP COLUMN IF EXISTS skill_name,
DROP COLUMN IF EXISTS skill_category,
DROP COLUMN IF EXISTS proficiency_level;

-- Also remove the confidence column as it's not used
ALTER TABLE memory_observations 
DROP COLUMN IF EXISTS confidence;

-- The table should now only have:
-- id, entity_id, observation_type, observation_value, source, tags, context, embedding, created_at