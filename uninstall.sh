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

print_header "GitAuto Uninstallation Script"

# ---------------------------
# Paths
# ---------------------------
VENV_DIR="$HOME/.gitauto_venv"
USER_LOCAL_BIN="$HOME/.local/bin"
TARGET="$USER_LOCAL_BIN/gitauto"
CONFIG_DIR="$HOME/.gitauto"
WORKDIR="$HOME/.gitauto_repo"

# ---------------------------
# Remove gitauto script
# ---------------------------
if [ -f "$TARGET" ]; then
    rm -f "$TARGET"
    print_success "Removed gitauto script at $TARGET"
else
    print_info "gitauto script not found at $TARGET"
fi

# ---------------------------
# Remove virtual environment
# ---------------------------
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    print_success "Removed virtual environment at $VENV_DIR"
else
    print_info "Virtual environment not found at $VENV_DIR"
fi

# ---------------------------
# Remove config
# ---------------------------
if [ -d "$CONFIG_DIR" ]; then
    read -p "Do you want to remove GitAuto config (~/.gitauto)? [y/N]: " remove_config
    if [[ "$remove_config" =~ ^[Yy]$ ]]; then
        rm -rf "$CONFIG_DIR"
        print_success "Removed config directory $CONFIG_DIR"
    else
        print_info "Config directory preserved"
    fi
else
    print_info "Config directory not found at $CONFIG_DIR"
fi

# ---------------------------
# Remove local repo clone
# ---------------------------
if [ -d "$WORKDIR" ]; then
    read -p "Do you want to remove the GitAuto repo clone (~/.gitauto_repo)? [y/N]: " remove_repo
    if [[ "$remove_repo" =~ ^[Yy]$ ]]; then
        rm -rf "$WORKDIR"
        print_success "Removed repository clone $WORKDIR"
    else
        print_info "Repository clone preserved"
    fi
else
    print_info "Repository clone not found at $WORKDIR"
fi

print_header "Uninstallation Complete!"
print_success "GitAuto has been removed from your system"
exit 0
