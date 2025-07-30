import os
DATABASE_URL_DIRECT = os.getenv('DATABASE_URL_DIRECT', 'sqlite+aiosqlite:///./test.db')
