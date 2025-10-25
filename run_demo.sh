#!/bin/bash
# ============================================================================
# Cryptocurrency Analytics Platform - Live Demo Setup
# ============================================================================

echo "════════════════════════════════════════════════════════════════════════"
echo "  🚀 CRYPTOCURRENCY ANALYTICS PLATFORM - LIVE DEMO"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo -e "${BLUE}Step 1: Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi
echo ""

# Step 2: Install dependencies
echo -e "${BLUE}Step 2: Installing required Python packages...${NC}"
echo "This may take a minute..."
pip install -q fastapi uvicorn pydantic sqlalchemy pytest numpy pandas python-jose[cryptography] 2>&1 | grep -v "Requirement already satisfied" || true
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 3: Check if demo script exists
echo -e "${BLUE}Step 3: Checking demo files...${NC}"
if [ -f "QUICK_DEMO.py" ]; then
    echo -e "${GREEN}✓ QUICK_DEMO.py found${NC}"
else
    echo -e "${RED}✗ QUICK_DEMO.py not found${NC}"
    exit 1
fi
echo ""

# Step 4: Run the demo
echo -e "${BLUE}Step 4: Running live demo...${NC}"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
python3 QUICK_DEMO.py
echo ""

# Step 5: Summary
echo "════════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ Demo completed!${NC}"
echo ""
echo "📖 Next steps:"
echo "  1. Review results above"
echo "  2. Check DEMO_RESULTS.md for detailed analysis"
echo "  3. Read VERIFICATION_REPORT.md for full project verification"
echo ""
echo "🐳 To run with full infrastructure (requires Docker):"
echo "  docker-compose up -d"
echo ""
echo "🧪 To run unit tests:"
echo "  pytest tests/ -v"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
