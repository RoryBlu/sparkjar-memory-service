-- Test script for actor validation trigger
-- Run this after applying add_actor_validation.sql to verify it works correctly

-- Test 1: Verify trigger exists
SELECT 'Test 1: Trigger exists' as test_name,
       EXISTS(
           SELECT 1 FROM pg_trigger 
           WHERE tgname = 'validate_actor_ref_entities'
       ) as result;

-- Test 2: Verify function exists
SELECT 'Test 2: Function exists' as test_name,
       EXISTS(
           SELECT 1 FROM pg_proc 
           WHERE proname = 'validate_actor_reference'
       ) as result;

-- Create test data
-- Note: These INSERTs will fail if the referenced actors don't exist
-- This is expected behavior and proves the validation works

DO $$
DECLARE
    test_client_id UUID := gen_random_uuid();
    test_human_id UUID := gen_random_uuid();
    test_synth_id UUID := gen_random_uuid();
    test_synth_class_id UUID := gen_random_uuid();
BEGIN
    -- Test 3: Insert with non-existent human actor (should fail)
    BEGIN
        INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type)
        VALUES (gen_random_uuid(), 'human', test_human_id, 'Test Entity', 'test');
        RAISE NOTICE 'Test 3 FAILED: Insert succeeded when it should have failed';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Test 3 PASSED: Insert correctly rejected - %', SQLERRM;
    END;

    -- Test 4: Insert with non-existent synth actor (should fail)
    BEGIN
        INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type)
        VALUES (gen_random_uuid(), 'synth', test_synth_id, 'Test Entity', 'test');
        RAISE NOTICE 'Test 4 FAILED: Insert succeeded when it should have failed';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Test 4 PASSED: Insert correctly rejected - %', SQLERRM;
    END;

    -- Test 5: Insert with non-existent synth_class actor (should fail)
    BEGIN
        INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type)
        VALUES (gen_random_uuid(), 'synth_class', test_synth_class_id, 'Test Entity', 'test');
        RAISE NOTICE 'Test 5 FAILED: Insert succeeded when it should have failed';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Test 5 PASSED: Insert correctly rejected - %', SQLERRM;
    END;

    -- Test 6: Insert with non-existent client actor (should fail)
    BEGIN
        INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type)
        VALUES (gen_random_uuid(), 'client', test_client_id, 'Test Entity', 'test');
        RAISE NOTICE 'Test 6 FAILED: Insert succeeded when it should have failed';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Test 6 PASSED: Insert correctly rejected - %', SQLERRM;
    END;

    -- Test 7: Insert with invalid actor_type (should fail)
    BEGIN
        INSERT INTO memory_entities (id, actor_type, actor_id, name, entity_type)
        VALUES (gen_random_uuid(), 'invalid_type', test_client_id, 'Test Entity', 'test');
        RAISE NOTICE 'Test 7 FAILED: Insert succeeded when it should have failed';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Test 7 PASSED: Insert correctly rejected - %', SQLERRM;
    END;
END $$;

-- Test 8: Verify metrics table exists and is empty (no successful validations yet)
SELECT 'Test 8: Metrics table' as test_name,
       EXISTS(SELECT 1 FROM actor_validation_metrics) as has_records,
       COUNT(*) as record_count
FROM actor_validation_metrics;

-- Summary
SELECT 'All tests completed. Check NOTICE messages above for validation test results.' as summary;