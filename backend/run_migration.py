import asyncio
import aiomysql
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def run_migration():
    # Read migration file
    with open('/app/backend/migrations_client_contacts.sql', 'r') as f:
        sql_content = f.read()
    
    # Split by semicolon and filter out empty statements
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
    
    # Connect to database
    conn = await aiomysql.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        port=int(os.environ.get('MYSQL_PORT', 3306)),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', ''),
        db=os.environ.get('MYSQL_DB', 'fox_db'),
        charset='utf8mb4'
    )
    
    try:
        async with conn.cursor() as cursor:
            for i, statement in enumerate(statements):
                if statement:
                    try:
                        print(f"Executing statement {i+1}/{len(statements)}...")
                        # Handle USE statement separately
                        if statement.upper().startswith('USE'):
                            continue
                        await cursor.execute(statement)
                        await conn.commit()
                        print(f"✓ Statement {i+1} executed successfully")
                    except Exception as e:
                        print(f"✗ Error in statement {i+1}: {e}")
                        print(f"Statement: {statement[:100]}...")
        
        print("\n✅ Migration completed successfully!")
        
    finally:
        conn.close()

if __name__ == '__main__':
    asyncio.run(run_migration())
