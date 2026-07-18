import os
import sys
from dotenv import load_dotenv

# Load the backend env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.core.database import engine
from sqlalchemy import text

def create_profiles_table():
    sql = """
    CREATE TABLE IF NOT EXISTS public.profiles (
        id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
        email TEXT,
        phone_number TEXT UNIQUE,
        telegram_chat_id TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
    );
    """
    with engine.begin() as conn:
        conn.execute(text(sql))
        print("Successfully created 'profiles' table.")

if __name__ == "__main__":
    create_profiles_table()
