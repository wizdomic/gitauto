#!/bin/bash

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

check_command() {
    command -v "$1" &> /dev/null
}

print_header "GitAuto Installation Script"

if [[ $EUID -eq 0 ]]; then
   print_error "This script should NOT be run as root/sudo"
   print_info "Please run without sudo: ./install.sh"
   exit 1
fi

print_info "Checking system requirements..."

# Check Python
if ! check_command python3; then
    print_error "Python 3 is not installed!"
    print_info "Please install Python 3.8 or higher:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "  macOS: brew install python3"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

tPYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
print_success "Python 3 found (version $PYTHON_VERSION)"

# Check pip
if ! check_command pip3; then
    print_error "pip3 is not installed!"
    print_info "Installing pip3..."
    if check_command apt-get; then
        sudo apt-get update && sudo apt-get install -y python3-pip
    elif check_command dnf; then
        sudo dnf install -y python3-pip
    elif check_command yum; then
        sudo yum install -y python3-pip
    else
        print_error "Please install pip3 manually"
        exit 1
    fi
fi

print_success "pip3 found"

# Check Git
if ! check_command git; then
    print_error "Git is not installed!"
    print_info "Please install Git:"
    echo "  Ubuntu/Debian: sudo apt-get install git"
    echo "  macOS: brew install git"
    echo "  Fedora: sudo dnf install git"
    exit 1
fi

print_success "Git found ($(git --version))"

# Check requirements.txt
# Move to the script's directory (important for VMs / automation)
cd "$(dirname "$0")" || exit 1

print_info "Checking for requirements.txt..."
if [ ! -f requirements.txt ]; then
    print_error "requirements.txt not found in $(pwd)!"
    print_info "Make sure you're running this script from the project root directory."
    exit 1
fi
print_success "requirements.txt found"

print_info "Installing Python dependencies..."

# Check if a virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    print_info "No virtual environment detected — installing with --user"
    if pip3 install --user -r requirements.txt; then
        print_success "Dependencies installed successfully (user site)"
    else
        print_error "Failed to install dependencies with --user"
        print_info "Try running inside a virtual environment or with sufficient permissions."
        exit 1
    fi
else
    print_info "Virtual environment detected — installing inside venv"
    if pip3 install -r requirements.txt; then
        print_success "Dependencies installed successfully (virtualenv)"
    else
        print_error "Failed to install dependencies in virtualenv"
        exit 1
    fi
fi


# === AI Setup Prompt for multi-provider ===
print_info "Optional: Enable AI-powered commit messages"

read -p "Would you like to enable AI features now? (y/N): " enable_ai

if [[ "$enable_ai" =~ ^[Yy]$ ]]; then
    echo "Supported AI providers:"
    echo "  1) anthropic (Claude)"
    echo "  2) openai (GPT)"
    echo "  3) gemini (coming soon)"
    read -p "Select AI provider [1-2]: " provider_choice

    case $provider_choice in
        1) provider="anthropic" ;;
        2) provider="openai" ;;
        *) print_error "Invalid choice, skipping AI setup." ;;
    esac

    if [[ "$provider" == "anthropic" || "$provider" == "openai" ]]; then
        read -p "Enter your $provider API key: " api_key
        CONFIG_DIR="$HOME/.gitauto"
        mkdir -p "$CONFIG_DIR"
        echo "provider=$provider" > "$CONFIG_DIR/config"
        echo "api_key=$api_key" >> "$CONFIG_DIR/config"
        chmod 600 "$CONFIG_DIR/config"
        print_success "API key and provider saved to $CONFIG_DIR/config"
    fi
else
    print_info "You can enable AI features later by running: gitauto setup"
fi
# =====================

# Install gitauto script
print_info "Setting up gitauto command..."
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"
cp gitauto.py "$INSTALL_DIR/gitauto"
chmod +x "$INSTALL_DIR/gitauto"
print_success "GitAuto installed to $INSTALL_DIR/gitauto"

# Add to PATH if needed
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    print_info "Adding $INSTALL_DIR to PATH..."

    SHELL_CONFIG=""
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        if [ -f "$HOME/.bashrc" ]; then
            SHELL_CONFIG="$HOME/.bashrc"
        elif [ -f "$HOME/.bash_profile" ]; then
            SHELL_CONFIG="$HOME/.bash_profile"
        fi
    fi

    if [ -n "$SHELL_CONFIG" ]; then
        if ! grep -q "$INSTALL_DIR" "$SHELL_CONFIG" 2>/dev/null; then
            echo "" >> "$SHELL_CONFIG"
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_CONFIG"
            print_success "Added to PATH in $SHELL_CONFIG"
            print_info "Please run: source $SHELL_CONFIG"
        fi
    else
        print_info "Please add this to your shell config manually:"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
fi

# Update current session PATH
export PATH="$HOME/.local/bin:$PATH"

print_header "Installation Complete!"

print_success "GitAuto is now installed!"
echo ""
print_info "Quick Start:"
echo "  1. Navigate to any git repository"
echo "  2. Run: gitauto"
echo "  3. Follow the interactive prompts"
echo ""
print_info "Optional: Enable AI-powered commit messages"
echo "  1. Get an API key from your provider's dashboard"
echo "  2. Run: gitauto setup"
echo "  3. Enter your API key and select provider"
echo ""
print_info "To test the installation, run:"
echo "  ./test.sh"
echo ""

if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    print_info "Don't forget to reload your shell or run:"
    echo "  source ~/.bashrc  (or ~/.zshrc)"
fi
