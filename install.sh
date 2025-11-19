#!/usr/bin/env bash
set -euo pipefail

# ----------------------------
# Colors
# ----------------------------
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

# ----------------------------
# Start installation
# ----------------------------
print_header "GitAuto Installation Script"

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    print_error "Do not run as root/sudo!"
    print_info "Run without sudo: ./install.sh"
    exit 1
fi

cd "$(dirname "$0")" || exit 1
WORKDIR="$(pwd)"

# ----------------------------
# Python 3 check
# ----------------------------
print_info "Locating Python 3..."
PYTHON=""
if check_command python3; then PYTHON=python3
elif check_command python; then
    if python -c 'import sys; sys.exit(0) if sys.version_info.major>=3 else sys.exit(1)'; then PYTHON=python; fi
fi
if [ -z "$PYTHON" ]; then
    print_error "Python 3 not found!"
    exit 1
fi
PY_VER="$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
print_success "Python found (version $PY_VER)"

# ----------------------------
# pip check
# ----------------------------
print_info "Locating pip..."
PIP=""
if check_command pip3; then PIP=pip3
elif check_command pip; then PIP=pip
elif $PYTHON -m pip --version &>/dev/null; then PIP="$PYTHON -m pip"
else
    print_error "pip not found. Please install pip."
    exit 1
fi
print_success "pip found ($PIP)"

# ----------------------------
# Git check
# ----------------------------
print_info "Checking Git..."
if ! check_command git; then
    print_error "Git is not installed!"
    exit 1
fi
print_success "Git found ($(git --version))"

# ----------------------------
# requirements.txt check
# ----------------------------
print_info "Checking for requirements.txt..."
if [ ! -f requirements.txt ]; then
    print_error "requirements.txt not found in $WORKDIR"
    exit 1
fi
print_success "requirements.txt found"

# ----------------------------
# Virtual environment
# ----------------------------
VENV_DIR="$HOME/.gitauto_venv"
if [ ! -d "$VENV_DIR" ]; then
    print_info "Creating virtual environment at $VENV_DIR..."
    $PYTHON -m venv "$VENV_DIR"
fi

# Activate venv
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
print_success "Virtual environment activated"

print_info "Upgrading pip and installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
print_success "Python dependencies installed"

# ----------------------------
# Install gitauto.py script
# ----------------------------
USER_LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$USER_LOCAL_BIN"
USER_TARGET="$USER_LOCAL_BIN/gitauto"

cp gitauto.py "$USER_TARGET"
chmod +x "$USER_TARGET"
print_success "Installed gitauto to $USER_TARGET"

# ----------------------------
# Update PATH if needed
# ----------------------------
update_shell_rc() {
    local rcfile="$1"
    local line='export PATH="$HOME/.local/bin:$PATH"'
    if [ -f "$rcfile" ] && ! grep -qF "$line" "$rcfile"; then
        echo "" >> "$rcfile"
        echo "# Added by GitAuto installer" >> "$rcfile"
        echo "$line" >> "$rcfile"
        print_success "Added PATH to $rcfile"
    fi
}

if [[ ":$PATH:" != *":$USER_LOCAL_BIN:"* ]]; then
    update_shell_rc "$HOME/.bashrc"
    update_shell_rc "$HOME/.bash_profile"
    update_shell_rc "$HOME/.zshrc"
    export PATH="$USER_LOCAL_BIN:$PATH"
    print_info "Reload shell or run: source ~/.bashrc"
fi

# ----------------------------
# Completion
# ----------------------------
print_header "Installation Complete!"
print_success "GitAuto installed to $USER_TARGET"
print_info "Activate virtual environment: source $VENV_DIR/bin/activate"
print_info "Run gitauto inside a git repository"
print_info "To configure AI: gitauto --setup"
exit 0
