#!/bin/bash

# BenchHub Plus Test Runner

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 BenchHub Plus Test Suite${NC}"
echo "================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Set environment variables for testing
export PYTHONPATH=$PWD:$PYTHONPATH
export TESTING=true
export DATABASE_URL="sqlite:///./test.db"
export OPENAI_API_KEY="test-key"
export CELERY_BROKER_URL="memory://"
export CELERY_RESULT_BACKEND="cache+memory://"

# Install test dependencies if needed
echo -e "${YELLOW}📦 Installing test dependencies...${NC}"
pip install -q pytest pytest-asyncio pytest-cov

# Clean up previous test artifacts
echo -e "${YELLOW}🧹 Cleaning up previous test artifacts...${NC}"
rm -f test.db
rm -rf .pytest_cache
rm -rf htmlcov
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Run tests with different configurations
TEST_FAILED=0

echo -e "${BLUE}🔬 Running Unit Tests${NC}"
echo "------------------------"
if python -m pytest tests/unit/ -v --tb=short; then
    echo -e "${GREEN}✅ Unit tests passed${NC}"
else
    echo -e "${RED}❌ Unit tests failed${NC}"
    TEST_FAILED=1
fi

echo -e "\n${BLUE}🔗 Running Integration Tests${NC}"
echo "--------------------------------"
if python -m pytest tests/integration/ -v --tb=short; then
    echo -e "${GREEN}✅ Integration tests passed${NC}"
else
    echo -e "${RED}❌ Integration tests failed${NC}"
    TEST_FAILED=1
fi

echo -e "\n${BLUE}🌐 Running End-to-End Tests${NC}"
echo "------------------------------"
if python -m pytest tests/e2e/ -v --tb=short; then
    echo -e "${GREEN}✅ End-to-end tests passed${NC}"
else
    echo -e "${RED}❌ End-to-end tests failed${NC}"
    TEST_FAILED=1
fi

# Run all tests with coverage
echo -e "\n${BLUE}📊 Running Coverage Analysis${NC}"
echo "-------------------------------"
if python -m pytest tests/ --cov=apps --cov-report=html --cov-report=term-missing --tb=short; then
    echo -e "${GREEN}✅ Coverage analysis completed${NC}"
    echo -e "${BLUE}📈 Coverage report generated in htmlcov/index.html${NC}"
else
    echo -e "${RED}❌ Coverage analysis failed${NC}"
    TEST_FAILED=1
fi

# Performance tests (optional)
if [ "$1" = "--performance" ]; then
    echo -e "\n${BLUE}⚡ Running Performance Tests${NC}"
    echo "------------------------------"
    python -m pytest tests/ -k "performance" -v --tb=short
fi

# Cleanup
echo -e "\n${YELLOW}🧹 Cleaning up test artifacts...${NC}"
rm -f test.db

# Summary
echo -e "\n${BLUE}📋 Test Summary${NC}"
echo "=================="

if [ $TEST_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed successfully!${NC}"
    echo -e "${BLUE}📊 View detailed coverage report: htmlcov/index.html${NC}"
    exit 0
else
    echo -e "${RED}💥 Some tests failed. Please check the output above.${NC}"
    exit 1
fi