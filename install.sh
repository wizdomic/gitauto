#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# GitAuto installer
# ============================================================

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print() { echo -e "${BLUE}==>${NC} $1"; }
success() { echo -e "${GREEN}✓ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
error() { echo -e "${RED}✗ $1${NC}"; }

check_command() { command -v "$1" &>/dev/null || return 1; }

# ---------------------------
# Safety & OS detection
# ---------------------------
print "GitAuto Installation Script"

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    error "Do not run as root/sudo!"
    exit 1
fi

UNAME="$(uname -s)"
case "$UNAME" in
    Linux) OS="linux" ;;
    Darwin) OS="macos" ;;
    MINGW*|MSYS*|CYGWIN*) OS="gitbash" ;;
    *) OS="unknown" ;;
esac
print "Detected OS: ${OS} (${UNAME})"

# ---------------------------
# Project root
# ---------------------------
cd "$(dirname "$0")" || exit 1
WORKDIR="$(pwd)"

# ---------------------------
# Python 3 check
# ---------------------------
print "Locating Python 3..."
PYTHON=""
if check_command python3; then PYTHON=python3
elif check_command python; then
    if python -c 'import sys; sys.exit(0) if sys.version_info.major>=3 else sys.exit(1)'; then PYTHON=python; fi
fi

if [ -z "$PYTHON" ]; then
    error "Python 3 not found!"
    exit 1
fi

PY_VER="$($PYTHON -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')"
success "Python found (version $PY_VER)"

# ---------------------------
# pip check
# ---------------------------
print "Locating pip..."
PIP=""
if check_command pip3; then PIP=pip3
elif check_command pip; then PIP=pip
elif $PYTHON -m pip --version &>/dev/null; then PIP="$PYTHON -m pip"
else
    error "pip not found. Please install pip."
    exit 1
fi
success "pip found ($PIP)"

# ---------------------------
# Git check
# ---------------------------
print "Checking Git..."
if ! check_command git; then
    error "Git is not installed!"
    exit 1
fi
success "Git found ($(git --version))"

# ---------------------------
# requirements.txt check
# ---------------------------
print "Checking for requirements.txt..."
if [ ! -f requirements.txt ]; then
    error "requirements.txt not found in $WORKDIR"
    exit 1
fi
success "requirements.txt found"

# ---------------------------
# Virtualenv detection
# ---------------------------
VENV_ACTIVE="no"
if [ -n "${VIRTUAL_ENV:-}" ] || [ "$($PYTHON -c 'import sys; print(sys.prefix != getattr(sys, \"base_prefix\", sys.prefix))')" = "True" ]; then
    VENV_ACTIVE="yes"
fi
print "Virtual environment active: $VENV_ACTIVE"

# ---------------------------
# Install dependencies
# ---------------------------
print "Installing Python dependencies..."
if [ "$VENV_ACTIVE" = "yes" ]; then
    $PIP install -r requirements.txt
    success "Dependencies installed inside virtualenv"
else
    $PIP install --user -r requirements.txt
    success "Dependencies installed to user site"
fi

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
print "User-local install: $USER_LOCAL_BIN. System install possible: $CAN_INSTALL_SYSTEM"

# ---------------------------
# Install gitauto script
# ---------------------------
SCRIPT_NAME="gitauto.py"
if [ ! -f "$SCRIPT_NAME" ]; then
    error "$SCRIPT_NAME not found in $WORKDIR"
    exit 1
fi

USER_TARGET="$USER_LOCAL_BIN/gitauto"
cp "$SCRIPT_NAME" "$USER_TARGET"
chmod +x "$USER_TARGET"
success "Installed user-local: $USER_TARGET"

if [ "$CAN_INSTALL_SYSTEM" = "yes" ]; then
    SYSTEM_TARGET="$SYSTEM_BIN/gitauto"
    cp "$SCRIPT_NAME" "$SYSTEM_TARGET"
    chmod +x "$SYSTEM_TARGET"
    success "Installed system-wide: $SYSTEM_TARGET"
elif [ "$CAN_INSTALL_SYSTEM" = "maybe" ]; then
    SYSTEM_TARGET="$SYSTEM_BIN/gitauto"
    print "Attempting system install with sudo..."
    if sudo cp "$SCRIPT_NAME" "$SYSTEM_TARGET" && sudo chmod +x "$SYSTEM_TARGET"; then
        success "Installed system-wide via sudo: $SYSTEM_TARGET"
    else
        warn "System install via sudo failed. Skipping."
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
        success "Added PATH to $rcfile"
    fi
}

if [[ ":$PATH:" != *":$USER_LOCAL_BIN:"* ]]; then
    update_shell_rc "$HOME/.bashrc"
    update_shell_rc "$HOME/.bash_profile"
    update_shell_rc "$HOME/.zshrc"
    export PATH="$USER_LOCAL_BIN:$PATH"
    print "Reload shell or run: source ~/.bashrc"
fi

# ---------------------------
# AI Setup
# ---------------------------
print "AI Setup (OpenAI / Anthropic / Gemini 2.5 flash)"
read -p "Enable AI for commit messages now? (y/N): " enable_ai
if [[ "$enable_ai" =~ ^[Yy]$ ]]; then
    echo ""
    echo "1) anthropic (Claude)"
    echo "2) openai (GPT)"
    echo "3) gemini (Google AI)"
    read -p "Select AI provider [1-3]: " choice
    case $choice in
        1) provider="anthropic" ;;
        2) provider="openai" ;;
        3) provider="gemini" ;;
        *) provider="" ;;
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
        success "$provider API key saved to $CONFIG_DIR/config.json"
    fi
fi

# ---------------------------
# Git Hooks Setup
# ---------------------------
print "Optional: Auto-install Git hooks in a repository"
read -p "Install Git hooks in current repo or path? (Enter for current, or path): " repo_path
if [ -z "$repo_path" ]; then repo_path="$(pwd)"; fi

if [ -d "$repo_path/.git" ]; then
    HOOK_DIR="$repo_path/.git/hooks"
    mkdir -p "$HOOK_DIR"

    # pre-commit
    cat > "$HOOK_DIR/pre-commit" <<'EOF'
#!/usr/bin/env bash
if command -v gitauto >/dev/null 2>&1; then
    gitauto --pre-commit
fi
EOF
    chmod +x "$HOOK_DIR/pre-commit"

    # commit-msg
    cat > "$HOOK_DIR/commit-msg" <<'EOF'
#!/usr/bin/env bash
if command -v gitauto >/dev/null 2>&1; then
    gitauto --commit-msg "$1"
fi
EOF
    chmod +x "$HOOK_DIR/commit-msg"
    success "Git hooks installed in $repo_path"
else
    warn "No git repo found at $repo_path. Skipping Git hooks."
fi

success "GitAuto installation complete!"
print "Run 'gitauto' inside a git repository to start automating commits."
exit 0
