#!/usr/bin/env python3
"""Combined Railway startup script that runs both internal and external APIs."""

import os
import sys
import logging
import asyncio
from multiprocessing import Process

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_internal_api():
    """Run the internal API."""
    try:
        from internal_api_railway import internal_app
        import uvicorn
        
        port = 8001
        logger.info(f"Starting internal API on port {port}")
        uvicorn.run(internal_app, host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Failed to start internal API: {e}")

def run_external_api():
    """Run the external API."""
    try:
        from external_api_railway import external_app
        import uvicorn
        
        port = int(os.getenv("PORT", "8443"))
        logger.info(f"Starting external API on port {port}")
        uvicorn.run(external_app, host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Failed to start external API: {e}")

def main():
    """Main function to start both APIs."""
    logger.info("Starting Railway Memory Service (Combined Mode)...")
    
    # Log environment
    logger.info(f"PORT: {os.getenv('PORT', 'not set')}")
    logger.info(f"DATABASE_URL: {'configured' if os.getenv('DATABASE_URL') else 'not set'}")
    
    # Determine which API to run based on PORT
    port = int(os.getenv("PORT", "8001"))
    
    if port == 8443 or port > 8000:
        # External API mode
        logger.info("Running in EXTERNAL API mode")
        run_external_api()
    else:
        # Internal API mode
        logger.info("Running in INTERNAL API mode")
        run_internal_api()

if __name__ == "__main__":
    main()