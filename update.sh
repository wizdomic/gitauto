#!/usr/bin/env bash
set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() { echo -e "\n${BLUE}============================${NC}\n  $1\n${BLUE}============================${NC}\n"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error()   { echo -e "${RED}✗ $1${NC}"; }
print_info()    { echo -e "${YELLOW}→ $1${NC}"; }

check_command() { command -v "$1" &>/dev/null || return 1; }

print_header "Updating GitAuto"

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    print_error "Do not run as root/sudo!"
    print_info "Run without sudo: ./update.sh"
    exit 1
fi

cd "$(dirname "$0")" || exit 1
WORKDIR="$(pwd)"

# ---------------------------
# Git check
# ---------------------------
print_info "Checking Git..."
if ! check_command git; then
    print_error "Git is not installed!"
    exit 1
fi
print_success "Git found ($(git --version))"

# ---------------------------
# Ensure this is a git repo
# ---------------------------
if [ ! -d ".git" ]; then
    print_error "This directory is not a git repository. Cannot auto-update."
    exit 1
fi

# ---------------------------
# Pull latest code
# ---------------------------
print_info "Fetching latest updates from Git..."
git fetch --all --tags
git reset --hard origin/$(git rev-parse --abbrev-ref HEAD)
print_success "Latest code fetched and applied"

# ---------------------------
# Copy all executable scripts to ~/.local/bin
# ---------------------------
USER_LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$USER_LOCAL_BIN"

# Copy any scripts from repo root that should be executable
for script in gitauto.py gitauto_*; do
    if [ -f "$script" ]; then
        cp "$script" "$USER_LOCAL_BIN/"
        chmod +x "$USER_LOCAL_BIN/$(basename "$script")"
        print_success "Updated $(basename "$script") to $USER_LOCAL_BIN"
    fi
done

print_header "Update Complete!"
print_info "Your existing configuration (AI keys, virtual environment) is untouched."
print_info "Run gitauto or other scripts from $USER_LOCAL_BIN inside a git repository."
exit 0
