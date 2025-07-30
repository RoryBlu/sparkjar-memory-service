#\!/usr/bin/env python3
"""
Check the actual schema of memory tables in the database.
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def check_memory_schema():
    """Check the actual schema of memory tables."""
    database_url = os.getenv("DATABASE_URL_DIRECT") or os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ No database URL found in environment")
        return
    
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Check memory_entities columns
            print("\n📋 memory_entities table schema:")
            result = await session.execute(text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = 'memory_entities'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            if columns:
                for col in columns:
                    nullable = "NULL" if col.is_nullable == "YES" else "NOT NULL"
                    default = f" DEFAULT {col.column_default}" if col.column_default else ""
                    print(f"   - {col.column_name}: {col.data_type} {nullable}{default}")
            else:
                print("   ❌ Table not found!")
            
            # Check for client_id column specifically
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'memory_entities' 
                AND column_name = 'client_id'
            """))
            
            if result.fetchone():
                print("\n⚠️  WARNING: client_id column still exists!")
            else:
                print("\n✅ Good: client_id column has been removed")
            
            # Check a few sample records
            print("\n📊 Sample memory_entities records:")
            result = await session.execute(text("""
                SELECT * FROM memory_entities
                LIMIT 3
            """))
            
            records = result.fetchall()
            if records:
                # Get column names
                columns = result.keys()
                print(f"\nColumns: {list(columns)}")
                
                for i, record in enumerate(records):
                    print(f"\nRecord {i+1}:")
                    for col, val in zip(columns, record):
                        if col == 'metadata' and val:
                            print(f"   {col}: <json data>")
                        else:
                            print(f"   {col}: {val}")
            else:
                print("   No records found")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("=" * 80)
    print("MEMORY SERVICE SCHEMA CHECK")
    print("=" * 80)
    
    asyncio.run(check_memory_schema())