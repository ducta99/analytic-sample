#!/bin/bash

echo "🗄️  Initializing PostgreSQL Database..."

cd /home/duc/analytics

# Start fresh postgres container
echo "Starting PostgreSQL container..."
docker-compose up -d postgres

echo "Waiting 10 seconds for PostgreSQL to initialize..."
sleep 10

# Test connection
echo "Testing connection..."
docker exec crypto-postgres psql -U crypto_user -d crypto_db -c "SELECT version();" | head -3

# Run migrations
echo "Running database migrations..."
docker exec -i crypto-postgres psql -U crypto_user -d crypto_db < migrations/001_initial_schema.sql 2>&1 | grep -v "ERROR\|NOTICE" | tail -10

# Verify tables
echo ""
echo "Verifying tables..."
docker exec crypto-postgres psql -U crypto_user -d crypto_db -c "\dt" | grep -E "users|coins|portfolios"

echo ""
echo "✅ Database initialized successfully!"
echo ""
echo "Testing asyncpg connection..."

python3 << 'EOF'
import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='crypto_user',
            password='crypto_password',
            database='crypto_db'
        )
        result = await conn.fetchval('SELECT COUNT(*) FROM coins')
        await conn.close()
        print(f"✅ Asyncpg connection SUCCESS! Found {result} coins")
        return 0
    except Exception as e:
        print(f"❌ Asyncpg connection FAILED: {e}")
        return 1

exit(asyncio.run(test()))
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Database is ready for services!"
else
    echo ""
    echo "⚠️  Database connection issue - may need manual fix"
fi
