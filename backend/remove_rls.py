import os
import sys
from dotenv import load_dotenv

# Load env before importing database engine
load_dotenv()

from sqlalchemy import text
from app.core.database import engine

tables = ['inventory', 'alert_rules', 'alerts', 'notification_logs']

try:
    with engine.begin() as conn:
        for table in tables:
            print(f"--- Processing {table} ---")
            
            # Check if table exists
            res = conn.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '{table}')"))
            if not res.scalar():
                print(f"Table {table} does not exist.")
                continue
            
            print("Dropping Policy...")
            conn.execute(text(f"DROP POLICY IF EXISTS \"{table}_isolation_policy\" ON {table};"))
            
            print("Disabling RLS...")
            conn.execute(text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;"))

            # Check user_id column
            res = conn.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'user_id')"))
            if res.scalar():
                print("Dropping user_id...")
                conn.execute(text(f"ALTER TABLE {table} DROP COLUMN user_id CASCADE;"))
            
            print(f"Finished {table}.\n")

    print("Migration successful.")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
