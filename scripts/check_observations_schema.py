#\!/usr/bin/env python3
"""Check memory_observations table schema."""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

async def check_schema():
    database_url = os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL")
    if not database_url:
        return
        
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check memory_observations columns
        print("\n📋 memory_observations table schema:")
        result = await session.execute(text("""
            SELECT 
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = 'memory_observations'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        if columns:
            for col in columns:
                nullable = "NULL" if col.is_nullable == "YES" else "NOT NULL"
                print(f"   - {col.column_name}: {col.data_type} {nullable}")
        else:
            print("   Table not found!")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_schema())