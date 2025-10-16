#!/bin/bash

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

cleanup() {
    if [ -d "$TEST_DIR" ]; then
        rm -rf "$TEST_DIR"
        print_info "Cleaned up test directory"
    fi
}

trap cleanup EXIT

print_header "GitAuto Test Suite"

TEST_DIR="/tmp/gitauto-test-$$"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

print_info "Test 1: Checking Python installation"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 not found"
    exit 1
fi

print_info "Test 2: Checking Git installation"
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    print_success "Git found: $GIT_VERSION"
else
    print_error "Git not found"
    exit 1
fi

print_info "Test 3: Checking gitauto command"
if command -v gitauto &> /dev/null; then
    print_success "gitauto command is available"
else
    print_error "gitauto command not found in PATH"
    print_info "Make sure you ran ./install.sh and reloaded your shell"
    exit 1
fi

print_info "Test 4: Checking Python dependencies"
if python3 -c "import anthropic" 2>/dev/null; then
    print_success "Anthropic library is installed"
else
    print_info "Anthropic library not found (optional, needed for AI features)"
fi

print_info "Test 5: Creating test git repository"
git init --quiet
git config user.name "Test User"
git config user.email "test@example.com"
print_success "Test repository created"

print_info "Test 6: Creating test files"
echo "# Test Project" > README.md
echo "print('Hello World')" > test.py
echo "test_output/" > .gitignore
print_success "Test files created"

print_info "Test 7: Testing git status detection"
STATUS=$(git status --short)
if [ -n "$STATUS" ]; then
    print_success "Git status detection working"
    echo "$STATUS" | sed 's/^/  /'
else
    print_error "Git status detection failed"
    exit 1
fi

print_info "Test 8: Testing git operations"
git add .
git commit -m "Initial commit" --quiet
print_success "Git add and commit working"

print_info "Test 9: Checking gitauto script permissions"
GITAUTO_PATH=$(which gitauto)
if [ -x "$GITAUTO_PATH" ]; then
    print_success "gitauto is executable"
else
    print_error "gitauto is not executable"
    exit 1
fi

print_info "Test 10: Testing gitauto script syntax"
if python3 -m py_compile "$GITAUTO_PATH" 2>/dev/null; then
    print_success "gitauto script syntax is valid"
else
    print_error "gitauto script has syntax errors"
    exit 1
fi

print_info "Test 11: Creating a test branch"
git checkout -b test-branch --quiet
git checkout main --quiet 2>/dev/null || git checkout master --quiet
print_success "Branch operations working"

print_info "Test 12: Testing configuration directory"
CONFIG_DIR="$HOME/.gitauto"
if [ -d "$CONFIG_DIR" ] || mkdir -p "$CONFIG_DIR"; then
    print_success "Configuration directory accessible"
else
    print_error "Cannot create configuration directory"
    exit 1
fi

print_info "Test 13: Making additional changes"
echo "" >> README.md
echo "## New Section" >> README.md
STATUS=$(git status --short)
if [ -n "$STATUS" ]; then
    print_success "Change detection working"
else
    print_error "Change detection failed"
    exit 1
fi

print_header "Test Summary"

print_success "All tests passed!"
echo ""
print_info "GitAuto is properly installed and ready to use"
echo ""
print_info "To use gitauto in any repository:"
echo "  1. cd /path/to/your/repo"
echo "  2. gitauto"
echo ""
print_info "To enable AI commit generation:"
echo "  1. Get API key from https://console.anthropic.com/"
echo "  2. Run: gitauto setup"
echo ""
print_info "Interactive test (optional):"
echo "  cd $TEST_DIR && gitauto"
echo "  (Test directory will be cleaned up automatically)"
echo ""
