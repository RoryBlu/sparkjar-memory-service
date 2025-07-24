-- Update actor_type constraints to support all actor types
-- This migration updates the CHECK constraints on memory_entities and memory_relations tables

-- Drop existing constraints
ALTER TABLE memory_entities DROP CONSTRAINT IF EXISTS memory_entities_actor_type_check;
ALTER TABLE memory_relations DROP CONSTRAINT IF EXISTS memory_relations_actor_type_check;

-- Add new constraints with all valid actor types
ALTER TABLE memory_entities 
ADD CONSTRAINT memory_entities_actor_type_check 
CHECK (actor_type IN ('human', 'synth', 'synth_class', 'client', 'skill_module', 'system'));

ALTER TABLE memory_relations 
ADD CONSTRAINT memory_relations_actor_type_check 
CHECK (actor_type IN ('human', 'synth', 'synth_class', 'client', 'skill_module', 'system'));

-- Add comment explaining actor types
COMMENT ON COLUMN memory_entities.actor_type IS 'Actor type: human (client_users), synth (synths), synth_class (synth_classes), client (clients), skill_module (skill_modules), system (internal)';
COMMENT ON COLUMN memory_relations.actor_type IS 'Actor type: human (client_users), synth (synths), synth_class (synth_classes), client (clients), skill_module (skill_modules), system (internal)';