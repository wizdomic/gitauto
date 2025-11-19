#!/usr/bin/env bash
set -euo pipefail

# ---------------------------
# Colors & helpers
# ---------------------------
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() { echo -e "\n${BLUE}================================================================${NC}\n  $1\n${BLUE}================================================================${NC}\n"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error()   { echo -e "${RED}✗ $1${NC}"; }
print_info()    { echo -e "${YELLOW}→ $1${NC}"; }

check_command() { command -v "$1" &>/dev/null || return 1; }

# ---------------------------
# Initial checks
# ---------------------------
print_header "GitAuto Update Script"

cd "$(dirname "$0")" || exit 1
WORKDIR="$(pwd)"

# ---------------------------
# Check if installed
# ---------------------------
USER_LOCAL_BIN="$HOME/.local/bin"
USER_TARGET="$USER_LOCAL_BIN/gitauto"

if [ ! -f "$USER_TARGET" ]; then
    print_error "GitAuto not found in $USER_TARGET"
    print_info "Please run install.sh first"
    exit 1
fi

# ---------------------------
# Backup current version
# ---------------------------
BACKUP="$USER_TARGET.bak"
cp "$USER_TARGET" "$BACKUP"
print_info "Backup of current gitauto saved at $BACKUP"

# ---------------------------
# Copy new version
# ---------------------------
cp gitauto.py "$USER_TARGET"
chmod +x "$USER_TARGET"
print_success "gitauto updated successfully to $USER_TARGET"

# ---------------------------
# Optional: Update dependencies
# ---------------------------
VENV_DIR="$HOME/.gitauto_venv"
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    print_info "Updating Python dependencies..."
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    print_success "Dependencies updated in virtual environment"
else
    print_info "Virtual environment not found. Skipping dependencies update."
fi

print_header "Update Complete!"
print_info "Run gitauto -v to verify version"
exit 0
