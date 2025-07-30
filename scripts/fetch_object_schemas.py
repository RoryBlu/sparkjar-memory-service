#!/usr/bin/env python3
"""Fetch object schemas from the database."""

import argparse
import asyncio
import json
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from services.crew_api.src.database.connection import get_direct_session


async def fetch_all() -> List[Dict[str, Any]]:
    """Return all rows from object_schemas ordered by name."""
    async with get_direct_session() as session:
        result = await session.execute(
            text(
                """
                SELECT id, name, object_type, schema, created_at, updated_at, version
                FROM object_schemas
                ORDER BY name
                """
            )
        )
        rows = result.mappings().all()
        return [dict(row) for row in rows]


async def main(output: Optional[str] = None) -> None:
    schemas = await fetch_all()
    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(schemas, f, indent=2, default=str)
    else:
        print(json.dumps(schemas, indent=2, default=str))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch object_schemas as JSON")
    parser.add_argument("-o", "--output", help="Write output to file")
    args = parser.parse_args()
    asyncio.run(main(args.output))
