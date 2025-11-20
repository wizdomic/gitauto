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

print_header()  { echo -e "\n${BLUE}===============================${NC}\n  $1\n${BLUE}===============================${NC}\n"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error()   { echo -e "${RED}✗ $1${NC}"; }
print_info()    { echo -e "${YELLOW}→ $1${NC}"; }

check_command() { command -v "$1" &>/dev/null || return 1; }


# OS detection
# ----------------------------
detect_os() {
    if [[ -f /etc/debian_version ]]; then
        OS="debian"
    elif [[ -f /etc/redhat-release ]]; then
        OS="redhat"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
}

suggest_install() {
    local tool="$1"

    case "$OS" in
        debian)
            case "$tool" in
                python) echo "Install Python 3: sudo apt update && sudo apt install -y python3 python3-venv python3-pip" ;;
                pip)    echo "Install pip: sudo apt update && sudo apt install -y python3-pip" ;;
                git)    echo "Install Git: sudo apt update && sudo apt install -y git" ;;
            esac
            ;;
        redhat)
            case "$tool" in
                python) echo "Install Python 3: sudo yum install -y python3 python3-venv python3-pip" ;;
                pip)    echo "Install pip: sudo yum install -y python3-pip" ;;
                git)    echo "Install Git: sudo yum install -y git" ;;
            esac
            ;;
        macos)
            case "$tool" in
                python|pip) echo "Install Python 3 and pip: brew install python" ;;
                git)        echo "Install Git: brew install git" ;;
            esac
            ;;
        windows)
            echo "Please install $tool manually from its official website." ;;
        *)
            echo "Unable to detect OS. Please install $tool manually." ;;
    esac
}


# Start Installation
# ----------------------------
print_header "Installing GitAuto"

# Prevent running as root
if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    print_error "Do not run as root/sudo!"
    print_info "Run without sudo: ./install.sh"
    exit 1
fi

detect_os

# Check if GitAuto is already installed
print_info "Checking if GitAuto is already installed..."
if command -v gitauto &>/dev/null; then
    if gitauto -v &>/dev/null; then
        print_success "GitAuto is already installed and available in your PATH."
        print_info "Installation aborted."
        exit 0
    fi
fi

cd "$(dirname "$0")" || exit 1
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORKDIR="$DIR"


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
    suggest_install python
    exit 1
fi
PY_VER="$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
print_success "Python found (version $PY_VER)"


# pip check
# ----------------------------
print_info "Locating pip..."
PIP=""
if check_command pip3; then PIP=pip3
elif check_command pip; then PIP=pip
elif $PYTHON -m pip --version &>/dev/null; then PIP="$PYTHON -m pip"
else
    print_error "pip not found!"
    suggest_install pip
    exit 1
fi
print_success "pip found ($PIP)"


# Git check
# ----------------------------
print_info "Checking Git..."
if ! check_command git; then
    print_error "Git is not installed!"
    suggest_install git
    exit 1
fi
print_success "Git found ($(git --version))"


# requirements.txt check
# ----------------------------
print_info "Checking for requirements.txt..."
if [ ! -f requirements.txt ]; then
    print_error "requirements.txt not found in $WORKDIR"
    exit 1
fi
print_success "requirements.txt found"


# Virtual environment for main dependencies
# ----------------------------
VENV_DIR="$HOME/.gitauto_venv"
if [ ! -d "$VENV_DIR" ]; then
    print_info "Creating virtual environment at $VENV_DIR..."
    $PYTHON -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
print_success "Virtual environment activated"

print_info "Upgrading pip and installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
print_success "Python dependencies installed"


# AI dedicated venv
# ----------------------------
AI_VENV="$HOME/.gitauto/ai_venv"
if [ ! -d "$AI_VENV" ]; then
    print_info "Creating dedicated AI virtual environment at $AI_VENV..."
    $PYTHON -m venv "$AI_VENV"
fi
source "$AI_VENV/bin/activate"

print_info "Installing AI libraries in dedicated venv..."
pip install --upgrade pip setuptools wheel
pip install openai anthropic google-generativeai
print_success "AI libraries installed in $AI_VENV"


# Install gitauto script
# ----------------------------
USER_LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$USER_LOCAL_BIN"
USER_TARGET="$USER_LOCAL_BIN/gitauto"

cp "$DIR/src/gitauto.py" "$USER_TARGET"
chmod +x "$USER_TARGET"
print_success "Installed gitauto to $USER_TARGET"

# Update PATH if needed
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


# Finish
# ----------------------------
print_header "Installation Complete!"
print_success "GitAuto installed to $USER_TARGET"
print_info "Activated virtual environment for GitAuto: source $VENV_DIR/bin/activate"
print_info "Configure AI keys: gitauto setup"
print_info "Run gitauto inside a git repository"
print_info "To Update Latest GitAuto: ./update.sh"
print_info "To Uninstall Completely: ./uninstall.sh"

exit 0
