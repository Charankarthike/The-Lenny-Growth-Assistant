#!/bin/bash
set -e

echo "======================================"
echo "The Lenny Growth Assistant"
echo "Pre-Deployment Verification Script"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    FAILURES=$((FAILURES + 1))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "1. Checking Project Structure..."
echo "=================================="

# Check key directories
if [ -d "backend" ]; then
    check_pass "backend/ directory exists"
else
    check_fail "backend/ directory missing"
fi

if [ -d "frontend" ]; then
    check_pass "frontend/ directory exists"
else
    check_fail "frontend/ directory missing"
fi

if [ -d "data/transcripts" ]; then
    check_pass "data/transcripts/ directory exists"
else
    check_fail "data/transcripts/ directory missing"
fi

if [ -d "docs" ]; then
    check_pass "docs/ directory exists"
else
    check_fail "docs/ directory missing"
fi

echo ""
echo "2. Checking Key Files..."
echo "=================================="

# Check essential files
files=(
    "README.md"
    "DEPLOYMENT.md"
    ".env.example"
    "docker-compose.yml"
    "backend/Dockerfile"
    "frontend/Dockerfile"
    "backend/requirements.txt"
    "frontend/package.json"
    "backend/app/main.py"
    "backend/app/config.py"
    "frontend/src/App.tsx"
    "scripts/init.sh"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file"
    else
        check_fail "$file missing"
    fi
done

echo ""
echo "3. Checking Documentation..."
echo "=================================="

docs=(
    "docs/PRD.md"
    "docs/architecture.md"
    "docs/design.md"
    "agent-transcripts/README.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        check_pass "$doc"
    else
        check_fail "$doc missing"
    fi
done

echo ""
echo "4. Checking Sample Data..."
echo "=================================="

if [ -f "data/transcripts/sample_episode_001.json" ]; then
    check_pass "Sample episode 1 exists"
else
    check_fail "Sample episode 1 missing"
fi

if [ -f "data/transcripts/sample_episode_002.json" ]; then
    check_pass "Sample episode 2 exists"
else
    check_fail "Sample episode 2 missing"
fi

echo ""
echo "5. Checking Environment Configuration..."
echo "=================================="

if [ -f ".env" ]; then
    check_warn ".env file exists (check for API keys)"
    
    # Check if API key is set
    if grep -q "ANTHROPIC_API_KEY=your_anthropic_api_key_here" .env 2>/dev/null; then
        check_warn "ANTHROPIC_API_KEY not configured (using placeholder)"
    elif grep -q "ANTHROPIC_API_KEY=" .env 2>/dev/null; then
        check_pass "ANTHROPIC_API_KEY is configured"
    else
        check_warn "ANTHROPIC_API_KEY not found in .env"
    fi
else
    check_warn ".env file not created yet (will need to copy from .env.example)"
fi

echo ""
echo "6. Checking Docker Setup..."
echo "=================================="

# Check if Docker is installed
if command -v docker &> /dev/null; then
    check_pass "Docker is installed"
    docker --version
else
    check_fail "Docker is not installed"
fi

# Check if Docker Compose is installed
if command -v docker-compose &> /dev/null; then
    check_pass "Docker Compose is installed"
    docker-compose --version
elif docker compose version &> /dev/null; then
    check_pass "Docker Compose (plugin) is installed"
    docker compose version
else
    check_fail "Docker Compose is not installed"
fi

# Check if Docker is running
if docker info &> /dev/null; then
    check_pass "Docker daemon is running"
else
    check_fail "Docker daemon is not running"
fi

echo ""
echo "7. Checking Scripts..."
echo "=================================="

if [ -x "scripts/init.sh" ]; then
    check_pass "scripts/init.sh is executable"
else
    if [ -f "scripts/init.sh" ]; then
        check_warn "scripts/init.sh exists but not executable (run: chmod +x scripts/init.sh)"
    else
        check_fail "scripts/init.sh missing"
    fi
fi

echo ""
echo "8. Backend Dependencies Check..."
echo "=================================="

if [ -f "backend/requirements.txt" ]; then
    dep_count=$(wc -l < "backend/requirements.txt" | tr -d ' ')
    check_pass "requirements.txt has $dep_count dependencies"
    
    # Check for key dependencies
    if grep -q "fastapi" "backend/requirements.txt"; then
        check_pass "FastAPI dependency present"
    fi
    if grep -q "sqlalchemy" "backend/requirements.txt"; then
        check_pass "SQLAlchemy dependency present"
    fi
    if grep -q "anthropic" "backend/requirements.txt"; then
        check_pass "Anthropic dependency present"
    fi
fi

echo ""
echo "9. Frontend Dependencies Check..."
echo "=================================="

if [ -f "frontend/package.json" ]; then
    check_pass "package.json exists"
    
    # Check for key dependencies
    if grep -q "react" "frontend/package.json"; then
        check_pass "React dependency present"
    fi
    if grep -q "typescript" "frontend/package.json"; then
        check_pass "TypeScript dependency present"
    fi
    if grep -q "zustand" "frontend/package.json"; then
        check_pass "Zustand dependency present"
    fi
fi

echo ""
echo "======================================"
echo "Verification Summary"
echo "======================================"

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Copy .env.example to .env: cp .env.example .env"
    echo "2. Edit .env and add your ANTHROPIC_API_KEY"
    echo "3. Run initialization: ./scripts/init.sh"
    echo ""
    exit 0
else
    echo -e "${RED}✗ $FAILURES check(s) failed${NC}"
    echo ""
    echo "Please fix the issues above before proceeding."
    echo ""
    exit 1
fi
