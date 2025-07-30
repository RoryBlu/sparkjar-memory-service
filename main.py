#!/usr/bin/env python3
"""Main entry point for Railway deployment."""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function to start the appropriate service."""
    port = int(os.getenv("PORT", "8001"))
    logger.info(f"Starting service on port {port}")
    
    if port > 8000:  # External API port
        logger.info("Starting EXTERNAL API")
        from external_api import external_app
        import uvicorn
        uvicorn.run(external_app, host="0.0.0.0", port=port)
    else:  # Internal API port
        logger.info("Starting INTERNAL API")
        from internal_api import internal_app
        import uvicorn
        uvicorn.run(internal_app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()