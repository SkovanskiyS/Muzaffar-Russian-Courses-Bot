import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def check_connection():
    try:
        # Get the DATABASE_URL from environment variables
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            print("DATABASE_URL environment variable is not set.")
            return

        # Create the async engine
        engine = create_async_engine(db_url)

        # Attempt to connect
        async with engine.connect() as conn:
            print("Connection successful!")
    except Exception as e:
        print(f"Error connecting to the database: {e}")
    finally:
        # It's good practice to dispose of the engine if it was created
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_connection())