# SparkJar Memory Service - Railway Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the SparkJar Memory Service (including Sequential Thinking APIs) on Railway. The service uses a three-interface architecture to handle Railway's IPv6 networking requirements.

## Prerequisites

Before deploying, ensure you have:
- A Railway account with a project created
- A PostgreSQL database (can be provisioned on Railway)
- Access to the SparkJar embeddings service or your own embeddings API
- A Supabase instance (for multi-tenant data)

## Architecture Overview

The Memory Service provides three interfaces:
1. **Internal API** (Port 8001) - IPv6 for high-performance internal communication
2. **External API** (Port 8443) - IPv4 for secure external access with JWT auth
3. **MCP Server** - Optional, for Claude Desktop integration

## Step-by-Step Deployment

### Step 1: Create Railway Services

You'll need to create **two separate Railway services** for the memory system:

#### A. Internal Memory API Service

1. In your Railway project, click **"New Service"**
2. Select **"GitHub Repo"** (or GitLab/Bitbucket)
3. Choose your repository
4. Configure the service:
   - **Service Name**: `memory-internal`
   - **Root Directory**: `/services/memory-service`
   - **Start Command**: `hypercorn internal-api:internal_app --bind [::]:8001`
   - **Port**: `8001`

#### B. External Memory API Service

1. Click **"New Service"** again
2. Select the same repository
3. Configure the service:
   - **Service Name**: `memory-external`
   - **Root Directory**: `/services/memory-service`
   - **Start Command**: `hypercorn external-api:external_app --bind 0.0.0.0:8443`
   - **Port**: `8443`

### Step 2: Configure Environment Variables

Add these environment variables to **BOTH** services:

#### Database Configuration
```bash
# PostgreSQL Connection (use Railway's DATABASE_URL if using Railway Postgres)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
```

#### Embeddings Service Configuration
```bash
# Internal Railway URL for embeddings service
EMBEDDINGS_API_URL=http://embeddings.railway.internal:8000
EMBEDDING_MODEL=Alibaba-NLP/gte-multilingual-base
EMBEDDING_DIMENSION=768
```

#### Security Configuration
```bash
# Generate a secure secret key
SECRET_KEY=your-very-secure-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### API Configuration
```bash
# For Internal Service
INTERNAL_API_HOST=::
INTERNAL_API_PORT=8001

# For External Service
EXTERNAL_API_HOST=0.0.0.0
EXTERNAL_API_PORT=8443
```

#### Optional Configuration
```bash
# Logging
LOG_LEVEL=INFO

# CORS (for external API)
CORS_ORIGINS=["https://your-frontend.com"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

### Step 3: Set Up Networking

#### For Internal Service:
1. Go to service settings
2. Under **Networking**, enable **"Private Networking"**
3. Note the internal URL: `memory-internal.railway.internal`

#### For External Service:
1. Go to service settings
2. Under **Networking**, click **"Generate Domain"**
3. This creates a public URL for external access

### Step 4: Database Setup

The memory service uses **Supabase** for its database, which includes pgvector support for embeddings.

#### Existing Tables
Your Supabase database should already have:
- `memory_entities` - Core entity storage (with observations as JSONB field)
- `memory_relations` - Entity relationships

#### Tables to Create
You need to create these tables for the Sequential Thinking feature:
- `thinking_sessions` - Sequential thinking sessions
- `thoughts` - Individual thoughts in sessions

#### Run Database Migrations

1. **Create Sequential Thinking tables**:
```bash
# This SQL file creates thinking_sessions and thoughts tables
psql $DATABASE_URL < sql/create_memory_schema.sql

# Create the get_next_thought_number function
psql $DATABASE_URL < sql/create_functions_and_views.sql
```

2. **Seed Schema Definitions**:
```bash
# IMPORTANT: Run these to populate object_schemas table
# These are required for schema validation to work

# Memory service schemas
python scripts/seed_memory_schemas.py

# Sequential thinking schemas
python scripts/seed_thinking_schemas.py
```

3. **Verify pgvector extension**:
```sql
-- Run this in Supabase SQL editor to verify pgvector is enabled
CREATE EXTENSION IF NOT EXISTS vector;
```

4. **Fix any column issues** (if upgrading):
```sql
-- If you had the old schema with confidence/skill fields
-- Run this to remove them
psql $DATABASE_URL < sql/fix_observations_table.sql
```

#### Current Architecture Notes
- The `memory_entities` table currently stores observations as JSONB
- For better performance with embeddings, observations could be moved to a separate table
- The memory service handles embedding storage via the embeddings field in memory_entities

**Important**: Railway PostgreSQL does **NOT** support pgvector, which is required for the embeddings functionality. Always use Supabase or another PostgreSQL instance with pgvector extension enabled.

### Step 5: Deploy the Services

1. Push your code to the repository
2. Railway will automatically build and deploy both services
3. Monitor the deployment logs for any errors

### Step 6: Verify Deployment

#### Check Health Endpoints:

Internal Service:
```bash
# From another Railway service
curl http://memory-internal.railway.internal:8001/health
```

External Service:
```bash
# From anywhere
curl https://your-memory-external.railway.app/health
```

#### Test Authentication (External API):

1. Get a JWT token:
```bash
curl -X POST https://your-memory-external.railway.app/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "your-client-uuid",
    "api_key": "your-api-key"
  }'
```

2. Test an endpoint:
```bash
curl https://your-memory-external.railway.app/memory/entities \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Run Post-Deployment Tests:

1. **Test Memory Operations**:
```bash
# Create an entity
curl -X POST http://memory-internal.railway.internal:8001/entities \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test-client-id",
    "actor_type": "human",
    "actor_id": "test-actor-id",
    "entities": [{
      "name": "Test Entity",
      "entityType": "test",
      "observations": [{
        "type": "fact",
        "value": "Deployment test",
        "source": "system"
      }]
    }]
  }'
```

2. **Test Sequential Thinking**:
```bash
# Create a thinking session
curl -X POST http://memory-internal.railway.internal:8001/api/v1/thinking/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "client_user_id": "test-user-id",
    "session_name": "Deployment Test",
    "problem_statement": "Verify thinking service works"
  }'
```

3. **Run Comprehensive Tests** (if you have pytest configured):
```bash
# SSH into the service
railway run -s memory-internal bash

# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/test_memory_e2e.py -v
pytest tests/test_thinking_e2e.py -v
pytest tests/test_schema_validation.py -v
```

### Step 7: Configure Other Services

For services that need to access the memory service internally:

```python
# In your crew-api or other internal services
MEMORY_SERVICE_URL = "http://memory-internal.railway.internal:8001"

# No authentication needed for internal API
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{MEMORY_SERVICE_URL}/entities",
        json={"entities": [...]}
    )
```

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SUPABASE_URL` | Supabase project URL | `https://abc.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | `eyJ...` |
| `EMBEDDINGS_API_URL` | Embeddings service URL | `http://embeddings.railway.internal:8000` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | `your-very-secure-secret-key` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration | `30` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins | `[]` |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | `100` |

## Troubleshooting

### Common Issues

#### 1. "Connection refused" errors
- Ensure services are binding to correct addresses (`::` for IPv6, `0.0.0.0` for IPv4)
- Check Railway's private networking is enabled
- Verify port numbers match configuration

#### 2. Database connection errors
- Check `DATABASE_URL` is correctly set
- Ensure database is accessible from Railway
- Verify database migrations have run

#### 3. Authentication failures
- Verify `SECRET_KEY` is the same across services
- Check JWT token hasn't expired
- Ensure correct scopes in token

#### 4. Embeddings service not reachable
- Verify embeddings service is deployed and running
- Check internal URL uses `.railway.internal` suffix
- Ensure private networking is enabled

### Debugging Commands

View logs:
```bash
railway logs -s memory-internal
railway logs -s memory-external
```

Connect to service:
```bash
railway run -s memory-internal bash
```

Test internal connectivity:
```bash
railway run -s memory-internal curl http://embeddings.railway.internal:8000/health
```

## Production Considerations

### 1. Scaling
- Railway automatically handles horizontal scaling
- Consider increasing dynos for high traffic
- Monitor memory usage and adjust limits

### 2. Security
- Always use HTTPS for external API
- Rotate `SECRET_KEY` periodically
- Implement rate limiting for external endpoints
- Use strong API keys

### 3. Monitoring
- Set up Railway's built-in metrics
- Monitor error rates and response times
- Set up alerts for service health

### 4. Backup
- Regular PostgreSQL backups
- Export memory graph periodically
- Document recovery procedures

## Next Steps

1. Test all three interfaces (internal, external, MCP)
2. Set up monitoring and alerts
3. Configure backup procedures
4. Document API keys and access patterns
5. Test sequential thinking endpoints

## Support

For issues specific to:
- **Railway deployment**: Check Railway docs or support
- **Memory service**: Create issue in sparkjar-crew repo
- **Networking**: Review Railway IPv6 guide in project root

## Quick Reference

### Internal API Access (from other Railway services):
```
http://memory-internal.railway.internal:8001
```

### External API Access (from anywhere):
```
https://your-memory-external.railway.app
```

### Health Check URLs:
- Internal: `http://memory-internal.railway.internal:8001/health`
- External: `https://your-memory-external.railway.app/health`

### Key API Endpoints:
- `/memory/entities` - Create/search entities
- `/memory/relations` - Manage relationships
- `/api/v1/thinking/sessions` - Sequential thinking
- `/auth/token` - Get JWT token (external only)