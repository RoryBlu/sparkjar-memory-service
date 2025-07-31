# Chain-of-Density (CoD) Workflow

This guide outlines how to ingest new content using the CoD process. It also notes the new zero-vector embedding behavior and the three-step ingestion pipeline.

## Overview

CoD summarizes incoming text with a short, dense description before full ingestion. The service then stores both the summary and the original text for retrieval.

## Three-Step Ingestion Process

1. **Chunk the text** – Split documents into manageable segments.
2. **Generate embeddings** – Create vector embeddings for each chunk. If an embedding service is unavailable, a zero-vector is inserted so indexes remain aligned.
3. **Store in memory** – Persist both the summary and original content in the knowledge graph.

## Prompt Examples

```text
"Summarize with CoD: {document_snippet}"
"Embed and store via CoD"
```

CoD summaries keep the memory graph lightweight while preserving detail in the original text.
