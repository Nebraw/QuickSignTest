#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display elapsed time
elapsed_time() {
    local duration=$1
    printf "%.2fs" "$duration"
}

# Function to run a step with timing
run_step() {
    local step_name=$1
    local command=$2
    
    echo -e "${BLUE}[→]${NC} ${step_name}..."
    start_time=$(date +%s.%N)
    
    if eval "$command" > /tmp/lint_output.txt 2>&1; then
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc)
        echo -e "${GREEN}[✓]${NC} ${step_name} - ${GREEN}Success${NC} ($(elapsed_time $duration))"
        cat /tmp/lint_output.txt
        return 0
    else
        end_time=$(date +%s.%N)
        duration=$(echo "$end_time - $start_time" | bc)
        echo -e "${RED}[✗]${NC} ${step_name} - ${RED}Failed${NC} ($(elapsed_time $duration))"
        cat /tmp/lint_output.txt
        return 1
    fi
}

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Code Quality Checks${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Run ruff
run_step "Running ruff check" "poetry run ruff check"
ruff_status=$?

echo ""

# Run mypy
run_step "Running mypy type check" "poetry run mypy . --config-file ./pyproject.toml --namespace-packages"
mypy_status=$?

echo ""
echo -e "${YELLOW}========================================${NC}"

# Summary
if [ $ruff_status -eq 0 ] && [ $mypy_status -eq 0 ]; then
    echo -e "${GREEN}[✓] All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}[✗] Some checks failed${NC}"
    exit 1
fi


echo "=========================================="
echo "API Tests"
echo "=========================================="
./run_test.sh