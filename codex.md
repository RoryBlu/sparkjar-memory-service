# Codex Guidelines

This repository follows a few standards for code and documentation changes.

## Coding Standards

- Keep code modular and avoid deep nesting.
- Follow the structure used in `services/` and `api/` for new modules.
- Use type hints and docstrings for all public methods.

## Testing and Linting

Run tests and linters whenever code changes are made. Documentation-only changes do not require tests.

```bash
# Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run linters
ruff .

# Run tests
pytest -v
```

Detailed instructions are available in [docs/TEST_DOCUMENTATION.md](docs/TEST_DOCUMENTATION.md).

## Reference Documents

- [Memory System Master Guide](docs/MEMORY_SYSTEM_MASTER_GUIDE.md)
- Specifications in `.codex/specs/memory_service_v2`

