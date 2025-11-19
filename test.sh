#!/bin/bash

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

success() { echo -e "${GREEN}✓ $1${NC}"; }
error()   { echo -e "${RED}✗ $1${NC}"; }
info()    { echo -e "${YELLOW}→ $1${NC}"; }

echo -e "\n========================================"
echo -e "         GitAuto Test & Auto-Fix"
echo -e "========================================\n"

INSTALL_DIR="$HOME/.local/bin"
BIN_PATH="$INSTALL_DIR/gitauto"

# -----------------------------
# Ensure install dir exists
# -----------------------------
info "Checking install directory..."
mkdir -p "$INSTALL_DIR"
success "Install directory OK"

# -----------------------------
# Check gitauto binary
# -----------------------------
info "Checking for gitauto binary..."
if [ ! -f "$BIN_PATH" ]; then
    error "gitauto binary missing"
    if [ -f "gitauto.py" ]; then
        info "Reinstalling from gitauto.py..."
        cp gitauto.py "$BIN_PATH"
        chmod +x "$BIN_PATH"
        success "gitauto reinstalled"
    else
        error "gitauto.py not found — cannot recover."
        exit 1
    fi
else
    success "gitauto binary OK"
fi

# -----------------------------
# Ensure executable
# -----------------------------
info "Checking executable permissions..."
chmod +x "$BIN_PATH"
success "Permissions OK"

# -----------------------------
# PATH Check
# -----------------------------
info "Checking PATH for ~/.local/bin..."
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    error "~/.local/bin is not in PATH"
    info "Add this to your shell:"
    echo 'export PATH="$HOME/.local/bin:$PATH"'
else
    success "~/.local/bin in PATH"
fi

# -----------------------------
# Dependency Check (venv-safe)
# -----------------------------
info "Checking Python dependencies..."

python3 << 'EOF'
import sys
try:
    import git
    print("OK")
except Exception:
    print("MISSING")
EOF

if [[ $? -ne 0 ]] || [[ "$(python3 - << 'EOF'
import sys
try:
    import git
    print("OK")
except:
    print("MISSING")
EOF
)" == "MISSING" ]]; then
    error "Missing Python dependencies"

    if [ -n "$VIRTUAL_ENV" ]; then
        info "Installing inside virtualenv..."
        pip install -r requirements.txt
        success "Dependencies installed inside venv"
    else
        info "Installing with --user..."
        pip3 install --user -r requirements.txt
        success "Dependencies installed (user)"
    fi
else
    success "Python dependencies OK"
fi

# -----------------------------
# AI CONFIG CHECK
# -----------------------------
info "Checking AI config..."
CONFIG="$HOME/.gitauto/config"

if [ ! -f "$CONFIG" ]; then
    info "Creating empty config..."
    mkdir -p "$HOME/.gitauto"
    touch "$CONFIG"
    chmod 600 "$CONFIG"
    success "AI config created"
else
    success "AI config exists"
fi

# -----------------------------
# Test gitauto command
# -----------------------------
info "Testing gitauto command..."
if gitauto --help >/dev/null 2>&1; then
    success "gitauto works!"
else
    error "gitauto failed — trying full path..."
    if "$BIN_PATH" --help >/dev/null 2>&1; then
        success "gitauto works via full path (PATH reload needed)"
    else
        error "gitauto is corrupted"
        exit 1
    fi
fi

echo ""
success "All tests passed!"
echo ""
