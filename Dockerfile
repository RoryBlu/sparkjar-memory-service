# services/memory-service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Copy shared modules
COPY ../../shared /app/shared
COPY ../crew-api/src/database/models.py /app/models.py

# Expose ports
EXPOSE 8001 8443

# Default to internal API
CMD ["hypercorn", "internal-api:internal_app", "--bind", "[::]:8001"]