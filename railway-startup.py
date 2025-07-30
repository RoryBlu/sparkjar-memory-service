#!/usr/bin/env python3
"""Railway startup script with error handling."""

import os
import sys
import logging

# Configure logging immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main startup function."""
    logger.info("Starting Railway Memory Service...")
    
    # Log environment
    port = os.getenv("PORT", "8001")
    logger.info(f"PORT: {port}")
    logger.info(f"DATABASE_URL: {'configured' if os.getenv('DATABASE_URL') else 'not set'}")
    logger.info(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'not set')}")
    
    try:
        # Import after logging is configured
        from internal_api import internal_app
        import uvicorn
        
        logger.info(f"Starting uvicorn on 0.0.0.0:{port}")
        uvicorn.run(
            internal_app,
            host="0.0.0.0",
            port=int(port),
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start service: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()