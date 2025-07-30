# Agent Guidelines

When modifying source code (excluding comment-only changes), run linters and tests:

```bash
ruff .
pytest -v
```

These checks are not required for documentation or comment-only edits.

See `codex.md` for full conventions. Key architecture references:
- [MEMORY_SYSTEM_MASTER_GUIDE.md](docs/MEMORY_SYSTEM_MASTER_GUIDE.md)
- [SCHEMA_VALIDATION_GUIDE.md](docs/SCHEMA_VALIDATION_GUIDE.md)

Remember the four-realm system (CLIENT, SYNTH_CLASS, SKILL_MODULE, SYNTH) and that all entity metadata must validate against `object_schemas`.
