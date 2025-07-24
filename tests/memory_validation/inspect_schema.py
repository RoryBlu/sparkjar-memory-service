#!/usr/bin/env python3
"""
Schema Inspector Runner

This script inspects the actual memory table schemas to understand
the current structure before running validation tests.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent

from tests.memory_validation.schema_inspector import SchemaInspector
from tests.memory_validation.base import setup_validation_logging

async def main():
    """Main inspection function."""
    # Set up logging
    logger = setup_validation_logging()
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL_DIRECT")
    if not database_url:
        print("❌ DATABASE_URL_DIRECT environment variable not set")
        print("Please set it to your database connection string")
        sys.exit(1)
    
    # Create schema inspector
    inspector = SchemaInspector(database_url)
    
    try:
        print("🔍 Inspecting memory table schemas...")
        
        # Run the inspection
        results = await inspector.run_validation()
        
        # Print the results
        if results and results[0].passed:
            print("✅ Schema inspection completed successfully!")
            inspector.print_schema_summary()
        else:
            print("❌ Schema inspection failed:")
            for result in results:
                if not result.passed:
                    print(f"   • {result.test_name}: {result.error_message}")
        
    except Exception as e:
        print(f"❌ Schema inspection failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())