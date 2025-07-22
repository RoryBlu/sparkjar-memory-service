#!/bin/bash
# Setup dedicated virtual environment for memory-service

echo "🔧 Setting up memory-service virtual environment..."

# Navigate to memory-service directory
cd /Users/r.t.rawlings/sparkjar-crew/services/memory-service

# Remove old venv if exists
if [ -d ".venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf .venv
fi

# Create new virtual environment
echo "Creating new virtual environment..."
python3.11 -m venv .venv || python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install core dependencies (no crewai conflicts here)
echo "Installing memory service dependencies..."
pip install \
    hypercorn==0.17.3 \
    fastapi==0.115.14 \
    pydantic==2.11.7 \
    sqlalchemy[asyncio]==2.0.41 \
    asyncpg==0.30.0 \
    pgvector==0.3.7 \
    python-dotenv==1.1.1 \
    httpx==0.28.1 \
    python-jose[cryptography]==3.3.0 \
    jsonschema==4.24.0

# Install from requirements.txt
echo "Installing from requirements.txt..."
pip install -r requirements.txt || echo "Some dependencies failed, but core packages are installed"

echo "✅ Virtual environment setup complete!"
echo "To activate: source services/memory-service/.venv/bin/activate"