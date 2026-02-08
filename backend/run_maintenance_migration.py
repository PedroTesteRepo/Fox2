import asyncio
import aiomysql
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def run_migration():
    conn = await aiomysql.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        db=os.environ.get('MYSQL_DB', 'fox_db'),
        charset='utf8mb4',
        autocommit=True
    )
    
    cursor = await conn.cursor()
    
    # Read migration file
    with open('/app/backend/migration_maintenance.sql', 'r') as f:
        sql = f.read()
    
    # Split by statements and execute
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
    
    for statement in statements:
        if statement and not statement.startswith('USE'):
            print(f"Executing: {statement[:100]}...")
            try:
                await cursor.execute(statement)
                print("✓ Success")
            except Exception as e:
                print(f"✗ Error: {e}")
    
    await cursor.close()
    conn.close()
    print("\n✅ Migration completed!")

if __name__ == "__main__":
    asyncio.run(run_migration())
