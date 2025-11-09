#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  QuickSign Test - Environment Setup${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Check if poetry is installed
echo -e "${BLUE}[→]${NC} Checking Poetry installation..."
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}[✗]${NC} Poetry is not installed!"
    echo -e "${YELLOW}Please install Poetry first:${NC}"
    echo -e "  curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
else
    echo -e "${GREEN}[✓]${NC} Poetry is installed"
fi

echo ""

# Check Python version
echo -e "${BLUE}[→]${NC} Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}[✓]${NC} Python ${python_version} detected"

echo ""

# Install dependencies
echo -e "${BLUE}[→]${NC} Installing dependencies with Poetry..."
if poetry install; then
    echo -e "${GREEN}[✓]${NC} Dependencies installed successfully"
else
    echo -e "${RED}[✗]${NC} Failed to install dependencies"
    exit 1
fi

echo ""

# Verify ruff installation
echo -e "${BLUE}[→]${NC} Verifying ruff installation..."
if poetry run ruff --version &> /dev/null; then
    ruff_version=$(poetry run ruff --version)
    echo -e "${GREEN}[✓]${NC} Ruff installed: ${ruff_version}"
else
    echo -e "${RED}[✗]${NC} Ruff installation failed"
    exit 1
fi

echo ""

# Verify mypy installation
echo -e "${BLUE}[→]${NC} Verifying mypy installation..."
if poetry run mypy --version &> /dev/null; then
    mypy_version=$(poetry run mypy --version)
    echo -e "${GREEN}[✓]${NC} Mypy installed: ${mypy_version}"
else
    echo -e "${RED}[✗]${NC} Mypy installation failed"
    exit 1
fi

echo ""

# Verify pytest installation
echo -e "${BLUE}[→]${NC} Verifying pytest installation..."
if poetry run pytest --version &> /dev/null; then
    pytest_version=$(poetry run pytest --version)
    echo -e "${GREEN}[✓]${NC} Pytest installed: ${pytest_version}"
else
    echo -e "${RED}[✗]${NC} Pytest installation failed"
    exit 1
fi

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${GREEN}[✓] Setup completed successfully!${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "You can now run:"
echo -e "  ${BLUE}./lint_module.sh${NC}  - Run code quality checks"
echo -e "  ${BLUE}./run_tests.sh${NC}   - Run tests"
echo ""
