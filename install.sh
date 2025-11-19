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

check_command() { command -v "$1" &>/dev/null || return 1; }

# ---------------------------
# Safety & OS detection
# ---------------------------
print_header "GitAuto Installation Script"

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    print_error "Do not run as root/sudo!"
    print_info "Run without sudo: ./install.sh"
    exit 1
fi

UNAME="$(uname -s)"
case "$UNAME" in
    Linux) OS="linux" ;;
    Darwin) OS="macos" ;;
    MINGW*|MSYS*|CYGWIN*) OS="gitbash" ;;
    *) OS="unknown" ;;
esac
print_info "Detected OS: ${OS} (${UNAME})"

# ---------------------------
# Project root
# ---------------------------
cd "$(dirname "$0")" || exit 1
WORKDIR="$(pwd)"

# ---------------------------
# Python 3 check
# ---------------------------
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

# ---------------------------
# pip check
# ---------------------------
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
# requirements.txt check
# ---------------------------
print_info "Checking for requirements.txt..."
if [ ! -f requirements.txt ]; then
    print_error "requirements.txt not found in $WORKDIR"
    exit 1
fi
print_success "requirements.txt found"

# ---------------------------
# Virtual environment setup
# ---------------------------
read -p "Do you want to use a virtual environment? (y/N): " use_venv
VENV_DIR="$HOME/.gitauto_venv"

if [[ "$use_venv" =~ ^[Yy]$ ]]; then
    if [ ! -d "$VENV_DIR" ]; then
        print_info "Creating virtual environment at $VENV_DIR..."
        $PYTHON -m venv "$VENV_DIR"
    fi
    print_info "Activating virtual environment..."
    # shellcheck disable=SC1090
    source "$VENV_DIR/bin/activate"
    print_success "Virtual environment activated"
    PIP="pip"
else
    print_info "Skipping virtual environment, using user-site install"
fi

# ---------------------------
# Install Python dependencies
# ---------------------------
print_info "Installing Python dependencies..."
$PIP install --upgrade pip setuptools wheel
$PIP install -r requirements.txt
print_success "Python dependencies installed"

# ---------------------------
# Install locations
# ---------------------------
USER_LOCAL_BIN="$HOME/.local/bin"
SYSTEM_BIN="/usr/local/bin"
mkdir -p "$USER_LOCAL_BIN"

CAN_INSTALL_SYSTEM="no"
if [ -d "$SYSTEM_BIN" ] && [ -w "$SYSTEM_BIN" ]; then
    CAN_INSTALL_SYSTEM="yes"
elif check_command sudo; then
    CAN_INSTALL_SYSTEM="maybe"
fi
print_info "User-local install: $USER_LOCAL_BIN. System install possible: $CAN_INSTALL_SYSTEM"

# ---------------------------
# Install gitauto script
# ---------------------------
SCRIPT_NAME="gitauto.py"
if [ ! -f "$SCRIPT_NAME" ]; then
    print_error "$SCRIPT_NAME not found in $WORKDIR"
    exit 1
fi

USER_TARGET="$USER_LOCAL_BIN/gitauto"
cp "$SCRIPT_NAME" "$USER_TARGET"
chmod +x "$USER_TARGET"
print_success "Installed user-local: $USER_TARGET"

if [ "$CAN_INSTALL_SYSTEM" = "yes" ]; then
    SYSTEM_TARGET="$SYSTEM_BIN/gitauto"
    cp "$SCRIPT_NAME" "$SYSTEM_TARGET"
    chmod +x "$SYSTEM_TARGET"
    print_success "Installed system-wide: $SYSTEM_TARGET"
elif [ "$CAN_INSTALL_SYSTEM" = "maybe" ]; then
    SYSTEM_TARGET="$SYSTEM_BIN/gitauto"
    print_info "Attempting system install with sudo..."
    if sudo cp "$SCRIPT_NAME" "$SYSTEM_TARGET" && sudo chmod +x "$SYSTEM_TARGET"; then
        print_success "Installed system-wide via sudo: $SYSTEM_TARGET"
    else
        print_info "System install via sudo failed. Skipping."
    fi
fi

# ---------------------------
# PATH update
# ---------------------------
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

# ---------------------------
# AI Setup (OpenAI, Anthropic, Gemini)
# ---------------------------
print_info "Optional: Enable AI-powered commit messages"
read -p "Enable AI now? (y/N): " enable_ai
if [[ "$enable_ai" =~ ^[Yy]$ ]]; then
    echo ""
    echo "1) OpenAI (GPT)"
    echo "2) Anthropic (Claude)"
    echo "3) Google Gemini"
    read -p "Select AI provider [1-3]: " choice
    case $choice in
        1) provider="openai" ;;
        2) provider="anthropic" ;;
        3) provider="gemini" ;;
        *) print_error "Invalid choice"; provider="" ;;
    esac

    if [[ -n "$provider" ]]; then
        read -p "Enter API key for $provider: " api_key
        CONFIG_DIR="$HOME/.gitauto"
        mkdir -p "$CONFIG_DIR"
        cat > "$CONFIG_DIR/config.json" <<EOF
{
    "provider": "$provider",
    "api_key": "$api_key"
}
EOF
        chmod 600 "$CONFIG_DIR/config.json"
        print_success "$provider API key saved to $CONFIG_DIR/config.json"
    fi
fi

# ---------------------------
# Git Hooks Setup
# ---------------------------
print_info "Optional: Auto-install Git hooks in repositories"
read -p "Install Git hooks in the current repo or specify path? (Enter for current, or path): " repo_path
if [ -z "$repo_path" ]; then
    repo_path="$(pwd)"
fi

if [ -d "$repo_path/.git" ]; then
    hook_dir="$repo_path/.git/hooks"
    mkdir -p "$hook_dir"

    # pre-commit hook
    cat > "$hook_dir/pre-commit" <<'EOF'
#!/usr/bin/env bash
if command -v gitauto >/dev/null 2>&1; then
    gitauto --pre-commit
fi
EOF
    chmod +x "$hook_dir/pre-commit"

    # commit-msg hook
    cat > "$hook_dir/commit-msg" <<'EOF'
#!/usr/bin/env bash
if command -v gitauto >/dev/null 2>&1; then
    gitauto --commit-msg "$1"
fi
EOF
    chmod +x "$hook_dir/commit-msg"

    print_success "Git hooks installed in $repo_path"
    print_info "Every commit will now trigger GitAuto automatically"
else
    print_info "No git repo found at $repo_path. Skipping Git hooks."
fi

print_header "Installation Complete!"
print_success "GitAuto installed to: $USER_TARGET"
if [ -n "${SYSTEM_TARGET:-}" ]; then
    print_success "Also installed system-wide: $SYSTEM_TARGET"
fi
print_info "Navigate to a git repo and run: gitauto"
exit 0
