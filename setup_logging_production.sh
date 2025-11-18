#!/bin/bash

# Production Logging Setup Script
# Run this on the production server to set up logging

set -e  # Exit on error

echo "================================"
echo "  AKILIMO Logging Setup"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/akilimon/ana_pro"
LOGS_DIR="${PROJECT_DIR}/logs"

echo -e "${YELLOW}Project Directory:${NC} $PROJECT_DIR"
echo -e "${YELLOW}Logs Directory:${NC} $LOGS_DIR"
echo ""

# Step 1: Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: This script must be run from the project root directory${NC}"
    echo "Expected to find manage.py in current directory"
    echo ""
    echo "Please run:"
    echo "  cd $PROJECT_DIR"
    echo "  bash setup_logging_production.sh"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found project directory"

# Step 2: Create logs directory
echo ""
echo "Creating logs directory..."
if [ -d "$LOGS_DIR" ]; then
    echo -e "${YELLOW}⚠${NC} Logs directory already exists"
else
    mkdir -p "$LOGS_DIR"
    echo -e "${GREEN}✓${NC} Created logs directory"
fi

# Step 3: Set permissions
echo ""
echo "Setting permissions..."
chmod 755 "$LOGS_DIR"
echo -e "${GREEN}✓${NC} Set directory permissions to 755"

# Step 4: Create .gitignore
echo ""
echo "Creating .gitignore for logs..."
cat > "${LOGS_DIR}/.gitignore" << 'EOF'
# Ignore all log files
*.log
*.log.*

# But keep this directory in git
!.gitignore
EOF
echo -e "${GREEN}✓${NC} Created .gitignore in logs directory"

# Step 5: Test write permissions
echo ""
echo "Testing write permissions..."
if touch "${LOGS_DIR}/test.log" 2>/dev/null; then
    rm "${LOGS_DIR}/test.log"
    echo -e "${GREEN}✓${NC} Write permissions OK"
else
    echo -e "${RED}✗${NC} Cannot write to logs directory"
    echo "You may need to run: chmod 755 $LOGS_DIR"
    exit 1
fi

# Step 6: Check Python environment
echo ""
echo "Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}✗${NC} Python not found"
    exit 1
fi
echo -e "${GREEN}✓${NC} Found Python: $PYTHON_CMD"

# Step 7: Verify Django settings
echo ""
echo "Verifying Django settings..."
if [ -f "akilimo_nigeria/settings/production.py" ]; then
    echo -e "${GREEN}✓${NC} Production settings found"
else
    echo -e "${RED}✗${NC} Production settings not found"
    exit 1
fi

# Step 8: Check middleware
echo ""
echo "Checking middleware..."
if [ -f "dashboard/middleware.py" ]; then
    echo -e "${GREEN}✓${NC} Error logging middleware found"
else
    echo -e "${YELLOW}⚠${NC} Middleware file not found - may need to deploy updated code"
fi

# Step 9: Show current logs
echo ""
echo "Current log files:"
if ls -lh "${LOGS_DIR}"/*.log 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Log files exist"
else
    echo -e "${YELLOW}⚠${NC} No log files yet (will be created on first request)"
fi

# Step 10: Display next steps
echo ""
echo "================================"
echo -e "${GREEN}  Setup Complete!${NC}"
echo "================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Restart your web application:"
echo -e "   ${YELLOW}touch tmp/restart.txt${NC}  # For Passenger"
echo ""
echo "2. Test logging by visiting your site:"
echo -e "   ${YELLOW}curl https://akilimonigeria.org/dashboard/${NC}"
echo ""
echo "3. Check if logs are being created:"
echo -e "   ${YELLOW}ls -lh $LOGS_DIR/${NC}"
echo ""
echo "4. View error logs:"
echo -e "   ${YELLOW}tail -f $LOGS_DIR/akilimo_nigeria_error.log${NC}"
echo ""
echo "5. Use the interactive log viewer:"
echo -e "   ${YELLOW}./view_logs.sh${NC}"
echo ""

# Optional: Show disk space
echo "Disk space available:"
df -h "$PROJECT_DIR" | tail -n 1

echo ""
echo "For troubleshooting, see: DEPLOYMENT_LOGGING_SETUP.md"
echo ""
