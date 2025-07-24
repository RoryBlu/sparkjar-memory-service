# Railway Monorepo Setup for Memory Service

## Overview

The memory service has three interfaces that need to be deployed as separate Railway services:

1. **memory-internal** - IPv6 internal API (port 8001)
2. **memory-external** - IPv4 external API (port 8443)
3. **memory-mcp** - MCP server (port 3000)

## Railway Configuration

### Common Settings for All Services

In Railway, set these for each service:

- **Root Directory**: `/` (repository root)
- **Watch Paths**: `services/memory-service/**,shared/**`

### Service-Specific Settings

#### 1. memory-internal (IPv6 Internal API)

- **Dockerfile Path**: `services/memory-service/Dockerfile.internal`
- **Start Command**: Leave empty (uses CMD from Dockerfile)
- **Port**: Railway will auto-detect 8001
- **Environment Variables**: Same as others

#### 2. memory-external (IPv4 External API)

- **Dockerfile Path**: `services/memory-service/Dockerfile.external`
- **Start Command**: Leave empty (uses CMD from Dockerfile)
- **Port**: Railway will auto-detect 8443
- **Environment Variables**: Same as others plus:
  - `API_SECRET_KEY`: Your JWT secret

#### 3. memory-mcp (MCP Server)

- **Dockerfile Path**: `services/memory-service/Dockerfile.mcp`
- **Start Command**: Leave empty (uses CMD from Dockerfile)
- **Port**: Railway will auto-detect 3000
- **Environment Variables**: Same as others

## Required Environment Variables

All services need these environment variables:

```env
# Database (Supabase)
DATABASE_URL_DIRECT=postgresql://...
DATABASE_URL_POOLED=postgresql://...

# ChromaDB (if using external ChromaDB)
CHROMA_URL=https://your-chromadb.railway.app
CHROMA_SERVER_AUTHN_CREDENTIALS=your-token

# API Authentication (for external API only)
API_SECRET_KEY=your-secret-key
```

## Dockerfile Explanations

### Why Three Dockerfiles?

1. **Dockerfile.internal** - Starts hypercorn with IPv6 binding `[::]:8001`
2. **Dockerfile.external** - Starts hypercorn with IPv4 binding `0.0.0.0:8443`
3. **Dockerfile.mcp** - Starts the MCP server on port 3000

All three Dockerfiles:
- Use the repository root as build context
- Copy the shared modules
- Copy the memory service code
- Set PYTHONPATH to include shared modules

## Deployment Order

1. Deploy memory-internal first
2. Deploy memory-external second
3. Deploy memory-mcp last (optional)

## Verification

After deployment, verify each service:

1. **Internal API**: Should show as running on Railway internal network
2. **External API**: Should be accessible via Railway public URL
3. **MCP Server**: Should be accessible for MCP clients

## Troubleshooting

### Build Fails with "not found" errors

- Ensure Root Directory is set to `/`
- Ensure Dockerfile path is correct
- Check that you're using the `.internal`, `.external`, or `.mcp` Dockerfiles

### Service Can't Find Shared Modules

- Check PYTHONPATH is set in Dockerfile
- Verify shared modules are being copied

### Database Connection Issues

- Verify DATABASE_URL_DIRECT and DATABASE_URL_POOLED are set
- Check if using correct pooled vs direct connection