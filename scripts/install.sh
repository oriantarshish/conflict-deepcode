#!/bin/bash

# DeepCode Installation Script
# This script installs DeepCode and its dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python
    if ! command_exists python3; then
        log_error "Python 3 is required but not installed."
        log_info "Please install Python 3.8 or later from https://python.org"
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    required_version="3.8"
    
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_error "Python ${required_version} or later is required. Found: ${python_version}"
        exit 1
    fi
    
    log_success "Python ${python_version} found"
    
    # Check pip
    if ! command_exists pip3 && ! command_exists pip; then
        log_error "pip is required but not installed."
        log_info "Please install pip: https://pip.pypa.io/en/stable/installation/"
        exit 1
    fi
    
    log_success "pip found"
}

# Install Ollama if not present
install_ollama() {
    if command_exists ollama; then
        log_success "Ollama is already installed"
        return 0
    fi
    
    log_info "Installing Ollama..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://ollama.ai/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew install ollama
        else
            log_warning "Homebrew not found. Please install Ollama manually from https://ollama.ai"
            return 1
        fi
    else
        log_warning "Unsupported OS. Please install Ollama manually from https://ollama.ai"
        return 1
    fi
    
    if command_exists ollama; then
        log_success "Ollama installed successfully"
    else
        log_error "Failed to install Ollama"
        return 1
    fi
}

# Start Ollama service
start_ollama() {
    log_info "Starting Ollama service..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux - start as service
        if command_exists systemctl; then
            sudo systemctl start ollama
            sudo systemctl enable ollama
        else
            nohup ollama serve > /dev/null 2>&1 &
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - start as background process
        if ! pgrep -x "ollama" > /dev/null; then
            nohup ollama serve > /dev/null 2>&1 &
            sleep 2
        fi
    fi
    
    # Wait for Ollama to be ready
    for i in {1..10}; do
        if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
            log_success "Ollama service is running"
            return 0
        fi
        log_info "Waiting for Ollama to start... ($i/10)"
        sleep 2
    done
    
    log_error "Failed to start Ollama service"
    return 1
}

# Pull DeepSeek model
pull_model() {
    log_info "Pulling DeepSeek Coder V2 model..."
    log_warning "This may take several minutes depending on your internet connection..."
    
    if ollama pull deepseek-coder-v2; then
        log_success "DeepSeek Coder V2 model downloaded successfully"
    else
        log_error "Failed to download DeepSeek Coder V2 model"
        return 1
    fi
}

# Install DeepCode
install_deepcode() {
    log_info "Installing DeepCode..."
    
    # Create virtual environment (optional but recommended)
    if [[ "${DEEPCODE_NO_VENV}" != "1" ]]; then
        log_info "Creating virtual environment..."
        python3 -m venv ~/.deepcode-venv
        source ~/.deepcode-venv/bin/activate
        log_success "Virtual environment created"
    fi
    
    # Install from PyPI (when available) or from source
    if [[ -f "setup.py" ]]; then
        # Install from source
        log_info "Installing from source..."
        pip install -e .
    else
        # Install from PyPI (future)
        log_info "Installing from PyPI..."
        pip install deepcode-ai
    fi
    
    log_success "DeepCode installed successfully"
}

# Create desktop entry (Linux only)
create_desktop_entry() {
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        return 0
    fi
    
    log_info "Creating desktop entry..."
    
    cat > ~/.local/share/applications/deepcode.desktop << EOF
[Desktop Entry]
Name=DeepCode
Comment=Free AI Coding Assistant
Exec=deepcode chat
Icon=terminal
Terminal=true
Type=Application
Categories=Development;
EOF
    
    log_success "Desktop entry created"
}

# Setup shell completion
setup_completion() {
    log_info "Setting up shell completion..."
    
    # Bash completion
    if [[ "$SHELL" == *"bash"* ]] && [[ -d ~/.bash_completion.d ]]; then
        deepcode --completion bash > ~/.bash_completion.d/deepcode
        log_success "Bash completion installed"
    fi
    
    # Zsh completion
    if [[ "$SHELL" == *"zsh"* ]] && [[ -d ~/.zsh/completions ]]; then
        mkdir -p ~/.zsh/completions
        deepcode --completion zsh > ~/.zsh/completions/_deepcode
        log_success "Zsh completion installed"
    fi
}

# Main installation function
main() {
    echo "🚀 DeepCode Installation Script"
    echo "================================"
    echo
    
    check_requirements
    echo
    
    install_ollama
    echo
    
    start_ollama
    echo
    
    pull_model
    echo
    
    install_deepcode
    echo
    
    create_desktop_entry
    setup_completion
    
    echo
    log_success "🎉 DeepCode installation completed!"
    echo
    echo "To get started:"
    echo "  1. Run: deepcode --help"
    echo "  2. Initialize a project: deepcode init"
    echo "  3. Start coding: deepcode chat"
    echo
    echo "For more information, visit: https://github.com/deepcode-ai/deepcode"
}

# Handle command line arguments
case "${1:-}" in
    --no-ollama)
        log_info "Skipping Ollama installation"
        check_requirements
        install_deepcode
        setup_completion
        ;;
    --ollama-only)
        log_info "Installing Ollama only"
        install_ollama
        start_ollama
        pull_model
        ;;
    --help|-h)
        echo "DeepCode Installation Script"
        echo
        echo "Usage: $0 [OPTIONS]"
        echo
        echo "Options:"
        echo "  --no-ollama    Skip Ollama installation"
        echo "  --ollama-only  Install Ollama only"
        echo "  --help, -h     Show this help message"
        echo
        echo "Environment Variables:"
        echo "  DEEPCODE_NO_VENV=1    Skip virtual environment creation"
        ;;
    *)
        main
        ;;
esac