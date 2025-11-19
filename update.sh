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

# ---------------------------
# Safety check
# ---------------------------
if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    print_error "Do not run as root/sudo!"
    print_info "Run without sudo: ./update.sh"
    exit 1
fi

print_header "GitAuto Auto-Update Script"

# ---------------------------
# Setup paths
# ---------------------------
WORKDIR="$HOME/.gitauto_repo"
VENV_DIR="$HOME/.gitauto_venv"
USER_LOCAL_BIN="$HOME/.local/bin"
TARGET="$USER_LOCAL_BIN/gitauto"
GIT_REPO_URL="https://github.com/wizdomic/PlatForm-Annotation.git"  # <-- replace with your repo

# ---------------------------
# Clone or pull repo
# ---------------------------
if [ ! -d "$WORKDIR/.git" ]; then
    print_info "Cloning GitAuto repository..."
    git clone "$GIT_REPO_URL" "$WORKDIR"
else
    print_info "Updating GitAuto repository..."
    cd "$WORKDIR"
    git fetch --all
    git reset --hard origin/main
    print_success "Repository updated"
fi

# ---------------------------
# Virtual environment
# ---------------------------
if [ ! -d "$VENV_DIR" ]; then
    print_info "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
print_success "Virtual environment activated"

# ---------------------------
# Install dependencies
# ---------------------------
if [ -f "$WORKDIR/requirements.txt" ]; then
    print_info "Installing/updating dependencies..."
    pip install --upgrade pip setuptools wheel
    pip install -r "$WORKDIR/requirements.txt"
    print_success "Dependencies updated"
else
    print_error "requirements.txt not found in $WORKDIR"
fi

# ---------------------------
# Install gitauto script
# ---------------------------
if [ -f "$WORKDIR/gitauto.py" ]; then
    print_info "Updating gitauto script..."
    mkdir -p "$USER_LOCAL_BIN"
    cp "$WORKDIR/gitauto.py" "$TARGET"
    chmod +x "$TARGET"
    print_success "gitauto script updated at $TARGET"
else
    print_error "gitauto.py not found in $WORKDIR"
fi

print_header "Auto-Update Complete!"
print_success "GitAuto is up-to-date!"
print_info "Virtual environment: $VENV_DIR"
print_info "Run 'gitauto' in a git repository to use it"
exit 0
