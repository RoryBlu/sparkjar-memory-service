# Codex Implementation Tasks for Memory Service v2

This file outlines the high level tasks for Codex agents to bring the new memory service specification to life.

1. **Unify Internal and External APIs**
   - Extract shared request/response schemas into a common module.
   - Ensure both FastAPI apps import the same validation logic.
2. **Refactor Tests**
   - Update existing unit tests to cover the new four-realm hierarchy logic.
   - Add integration tests for entity/observation validation and authentication.
3. **Database Migration**
   - Create migration scripts for any new tables or fields required by v2.
   - Verify backward compatibility with existing data.
4. **Deployment Updates**
   - Review Dockerfiles and Railway configs to support the combined API modules.
   - Add environment variables for internal secrets and API tokens.
5. **Documentation**
   - Update API reference docs to match v2 endpoints and response formats.
   - Provide usage examples demonstrating cross-realm queries.

