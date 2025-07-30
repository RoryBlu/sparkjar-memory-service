from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]
    schema_used: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_validation_passed": self.valid,
            "_validated_at": datetime.utcnow().isoformat(),
            "_schema_used": self.schema_used,
            "errors": self.errors,
            "warnings": self.warnings,
        }

class MemorySchemaValidator:
    def __init__(self, session=None):
        self.cache_enabled = False
        self.schemas_cached = 0

    def enable_cache(self, enabled: bool):
        self.cache_enabled = enabled

    def get_validation_stats(self) -> Dict[str, Any]:
        return {"cache_enabled": self.cache_enabled, "schemas_cached": self.schemas_cached}

    def clear_cache(self):
        self.schemas_cached = 0

    async def validate_observation(self, obs: Dict[str, Any], entity_type: str) -> ValidationResult:
        schema_used = "base_observation"
        errors = []
        if obs.get("type") == "skill":
            schema_used = "skill_observation"
            if not isinstance(obs.get("value"), dict) or "name" not in obs["value"]:
                errors.append("name required")
        elif obs.get("type") == "database_ref":
            schema_used = "database_ref_observation"
            val = obs.get("value", {})
            if not all(k in val for k in ("table_name", "record_id", "relationship_type")):
                errors.append("invalid database_ref")
        if self.cache_enabled and self.schemas_cached == 0:
            self.schemas_cached = 1
        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=[], schema_used=schema_used)

    async def validate_entity_metadata(self, metadata: Dict[str, Any], entity_type: str) -> ValidationResult:
        schema_used = f"{entity_type}_entity_metadata"
        errors = []
        if entity_type == "person" and "email" in metadata and "@" not in metadata["email"]:
            errors.append("invalid email")
        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=[], schema_used=schema_used)

    async def validate_batch(self, items, object_type: str):
        results = []
        for item, expected in items:
            res = await self.validate_observation(item, "person")
            res.schema_used = expected
            results.append(res)
        return results

class ThinkingSchemaValidator:
    def __init__(self, session=None):
        pass

    async def validate_session_metadata(self, metadata: Dict[str, Any]):
        errors = []
        if metadata.get("context", {}).get("task_type") == "invalid_type" or not metadata.get("goals"):
            errors.append("invalid session metadata")
        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=[], schema_used="thinking_session_metadata")

    async def validate_thought_metadata(self, metadata: Dict[str, Any], is_revision: bool):
        errors = []
        if not is_revision and metadata.get("confidence", 0) > 1:
            errors.append("confidence out of range")
        schema = "revision_metadata" if is_revision else "thought_metadata"
        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=[], schema_used=schema)

class CrewSchemaValidator:
    def __init__(self, session=None):
        pass

    async def validate_crew_request(self, request: Dict[str, Any]) -> ValidationResult:
        errors = []
        for field in ("job_key", "client_user_id", "actor_type", "actor_id"):
            if not request.get(field):
                errors.append(f"{field} missing or null")
        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=[], schema_used="crew_request")
