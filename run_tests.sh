#!/bin/bash
# Run memory service tests with proper environment setup

# Load environment from main .env file
set -a
source /Users/r.t.rawlings/sparkjar-crew/.env
set +a

# Map environment variables to what memory service expects
export SECRET_KEY="${API_SECRET_KEY}"
export SUPABASE_SERVICE_KEY="${SUPABASE_SECRET_KEY}"

# Set Python path to include service directory AND project root for shared modules
export PYTHONPATH="/Users/r.t.rawlings/sparkjar-crew:/Users/r.t.rawlings/sparkjar-crew/services/memory-service:$PYTHONPATH"

# Run tests
cd /Users/r.t.rawlings/sparkjar-crew/services/memory-service
/Users/r.t.rawlings/sparkjar-crew/.venv/bin/python -m pytest tests/ -v "$@"