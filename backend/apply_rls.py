import os
import sys
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
                
            print("Wiping data...")
            conn.execute(text(f"DELETE FROM {table};"))
            
            # Check user_id column
            res = conn.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'user_id')"))
            if not res.scalar():
                print("Adding user_id...")
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN user_id UUID REFERENCES auth.users(id) NOT NULL;"))
            
            if table == 'inventory':
                res = conn.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = '{table}' AND column_name = 'created_at')"))
                if not res.scalar():
                    print("Adding created_at...")
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now());"))
                    
            print("Enabling RLS...")
            conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
            
            print("Creating Policy...")
            conn.execute(text(f"DROP POLICY IF EXISTS \"{table}_isolation_policy\" ON {table};"))
            conn.execute(text(f"CREATE POLICY \"{table}_isolation_policy\" ON {table} FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);"))
            
            print(f"Finished {table}.\n")

    print("Migration successful.")
except Exception as e:
    print(f"Error: {e}")
