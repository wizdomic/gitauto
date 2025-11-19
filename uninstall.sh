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

# ---------------------------
# Uninstallation
# ---------------------------
print_header "GitAuto Uninstallation Script"

USER_LOCAL_BIN="$HOME/.local/bin"
USER_TARGET="$USER_LOCAL_BIN/gitauto"

if [ -f "$USER_TARGET" ]; then
    rm "$USER_TARGET"
    print_success "Removed $USER_TARGET"
else
    print_info "gitauto not found in $USER_TARGET"
fi

VENV_DIR="$HOME/.gitauto_venv"
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    print_success "Removed virtual environment at $VENV_DIR"
else
    print_info "Virtual environment not found, skipping"
fi

CONFIG_DIR="$HOME/.gitauto"
if [ -d "$CONFIG_DIR" ]; then
    rm -rf "$CONFIG_DIR"
    print_success "Removed configuration directory at $CONFIG_DIR"
else
    print_info "Configuration directory not found, skipping"
fi

print_header "Uninstallation Complete!"
print_info "Remove PATH entry in shell rc files manually if needed"
exit 0
