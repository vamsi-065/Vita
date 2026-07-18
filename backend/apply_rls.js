const { Client } = require('pg');
require('dotenv').config({ path: '.env' });

async function migrate() {
    if (!process.env.DATABASE_URL) {
        console.error('DATABASE_URL is missing in .env');
        process.exit(1);
    }

    const client = new Client({
        connectionString: process.env.DATABASE_URL,
    });

    try {
        await client.connect();
        console.log("Connected to the database.");

        const tablesToMigrate = ['inventory', 'alert_rules', 'alerts', 'notification_logs'];

        for (const table of tablesToMigrate) {
            console.log(`\n--- Processing table: ${table} ---`);
            
            // 1. Check if table exists
            const tableExistsResult = await client.query(`
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                );
            `, [table]);

            if (!tableExistsResult.rows[0].exists) {
                console.log(`Table '${table}' does not exist. Skipping.`);
                continue;
            }

            // 2. Wipe existing data
            console.log(`Deleting all existing data from '${table}'...`);
            await client.query(`DELETE FROM ${table};`);

            // 3. Add user_id column if it doesn't exist
            const columnExistsResult = await client.query(`
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = $1 AND column_name = 'user_id'
                );
            `, [table]);

            if (!columnExistsResult.rows[0].exists) {
                console.log(`Adding 'user_id' column to '${table}'...`);
                await client.query(`ALTER TABLE ${table} ADD COLUMN user_id UUID REFERENCES auth.users(id) NOT NULL;`);
            } else {
                console.log(`'user_id' column already exists in '${table}'.`);
            }
            
            // For inventory, ensure created_at exists
            if (table === 'inventory') {
                const createdColumnExists = await client.query(`
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = $1 AND column_name = 'created_at'
                    );
                `, [table]);
                if (!createdColumnExists.rows[0].exists) {
                    console.log(`Adding 'created_at' column to '${table}'...`);
                    await client.query(`ALTER TABLE ${table} ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now());`);
                }
            }

            // 4. Enable Row Level Security
            console.log(`Enabling RLS on '${table}'...`);
            await client.query(`ALTER TABLE ${table} ENABLE ROW LEVEL SECURITY;`);

            // 5. Drop existing policies to be safe
            console.log(`Dropping existing policies on '${table}'...`);
            await client.query(`DROP POLICY IF EXISTS "${table}_isolation_policy" ON ${table};`);

            // 6. Create universal CRUD policy for the table based on auth.uid()
            console.log(`Creating RLS policy '${table}_isolation_policy'...`);
            await client.query(`
                CREATE POLICY "${table}_isolation_policy" ON ${table}
                FOR ALL 
                USING (auth.uid() = user_id)
                WITH CHECK (auth.uid() = user_id);
            `);
            console.log(`Finished processing '${table}'.`);
        }

        console.log("\nMigration completed successfully.");

    } catch (err) {
        console.error("Migration failed:", err);
    } finally {
        await client.end();
    }
}

migrate();
