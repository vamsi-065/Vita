import pg from 'pg';
import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(process.cwd(), '../backend/.env') });

const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  console.error("DATABASE_URL is missing in backend/.env");
  process.exit(1);
}

const client = new pg.Client({
  connectionString: connectionString,
});

async function run() {
  await client.connect();
  const sql = `
    CREATE TABLE IF NOT EXISTS public.profiles (
        id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
        email TEXT,
        phone_number TEXT UNIQUE,
        telegram_chat_id TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
    );
  `;
  try {
    await client.query(sql);
    console.log("Successfully created profiles table.");
  } catch (err) {
    console.error("Error creating table:", err);
  } finally {
    await client.end();
  }
}

run();
