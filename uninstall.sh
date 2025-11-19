#!/usr/bin/env bash
set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() { echo -e "\n${BLUE}================================================================${NC}\n  $1\n${BLUE}================================================================${NC}\n"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error()   { echo -e "${RED}✗ $1${NC}"; }
print_info()    { echo -e "${YELLOW}→ $1${NC}"; }

print_header "GitAuto Uninstall Script"

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    print_error "Do not run as root/sudo!"
    print_info "Run without sudo: ./uninstall.sh"
    exit 1
fi

# Paths
USER_LOCAL_BIN="$HOME/.local/bin/gitauto"
VENV_DIR="$HOME/.gitauto_venv"
CONFIG_DIR="$HOME/.gitauto"

# Remove gitauto script
if [ -f "$USER_LOCAL_BIN" ]; then
    rm -f "$USER_LOCAL_BIN"
    print_success "Removed $USER_LOCAL_BIN"
else
    print_info "$USER_LOCAL_BIN not found, skipping"
fi

# Remove virtual environment
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    print_success "Removed virtual environment at $VENV_DIR"
else
    print_info "$VENV_DIR not found, skipping"
fi

# Remove config folder
if [ -d "$CONFIG_DIR" ]; then
    rm -rf "$CONFIG_DIR"
    print_success "Removed configuration folder at $CONFIG_DIR"
else
    print_info "$CONFIG_DIR not found, skipping"
fi

print_header "Uninstallation Complete!"
print_info "All GitAuto files removed from your home directory"
exit 0
