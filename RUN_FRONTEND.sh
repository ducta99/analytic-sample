#!/bin/bash

echo "================================================"
echo "🎨 Starting Cryptocurrency Analytics Frontend"
echo "================================================"

cd /home/duc/analytics/frontend

echo ""
echo "📋 Step 1: Checking Node.js and npm..."
echo "----------------------------------------"

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed!"
    echo "Please install Node.js 18+ first: https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"

echo ""
echo "📋 Step 2: Installing Dependencies..."
echo "----------------------------------------"

if [ ! -d "node_modules" ]; then
    echo "Installing packages (this may take a few minutes)..."
    npm install --legacy-peer-deps
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "📋 Step 3: Setting Environment Variables..."
echo "----------------------------------------"

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local..."
    cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8002/ws
NODE_ENV=development
EOF
    echo "✅ .env.local created"
else
    echo "✅ .env.local already exists"
fi

echo ""
echo "📋 Step 4: Starting Development Server..."
echo "----------------------------------------"

echo ""
echo "🚀 Starting Next.js on http://localhost:3000"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""
echo "================================================"
echo ""

# Start the dev server
npm run dev
