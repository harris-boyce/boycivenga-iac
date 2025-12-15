#!/bin/bash
#
# Bootstrap script for setting up development environment
# This script installs all necessary tools for working with this IaC repository
#
# Note: If you're using the devcontainer, these tools are already installed.
# This script is for users who prefer to work outside the devcontainer.

set -e

# Version configuration
TERRAFORM_VERSION="1.7.5"
DOCKER_COMPOSE_VERSION="v2.24.7"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo -e "${RED}Unsupported OS: $OSTYPE${NC}"
    echo "This script supports Linux and macOS only."
    exit 1
fi

echo -e "${GREEN}Detected OS: $OS${NC}"

# Check if running with appropriate permissions
if [[ "$OS" == "linux" ]]; then
    if [[ $EUID -eq 0 ]]; then
        echo -e "${YELLOW}Warning: Running as root. This is not recommended.${NC}"
    fi
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Terraform
install_terraform() {
    if command_exists terraform; then
        echo -e "${GREEN}Terraform is already installed: $(terraform version | head -n1)${NC}"
        return
    fi

    echo "Installing Terraform..."

    if [[ "$OS" == "linux" ]]; then
        curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" -o /tmp/terraform.zip
        unzip -o /tmp/terraform.zip -d /tmp
        sudo mv /tmp/terraform /usr/local/bin/
        rm /tmp/terraform.zip
    elif [[ "$OS" == "macos" ]]; then
        if command_exists brew; then
            brew install terraform
        else
            echo -e "${YELLOW}Homebrew not found. Installing Terraform manually...${NC}"
            ARCH=$(uname -m)
            if [[ "$ARCH" == "arm64" ]]; then
                TERRAFORM_ARCH="darwin_arm64"
            else
                TERRAFORM_ARCH="darwin_amd64"
            fi
            curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_${TERRAFORM_ARCH}.zip" -o /tmp/terraform.zip
            unzip -o /tmp/terraform.zip -d /tmp
            sudo mv /tmp/terraform /usr/local/bin/
            rm /tmp/terraform.zip
        fi
    fi

    echo -e "${GREEN}Terraform installed: $(terraform version | head -n1)${NC}"
}

# Install Python
install_python() {
    if command_exists python3; then
        echo -e "${GREEN}Python3 is already installed: $(python3 --version)${NC}"
    else
        echo "Installing Python3..."
        if [[ "$OS" == "linux" ]]; then
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv
        elif [[ "$OS" == "macos" ]]; then
            if command_exists brew; then
                brew install python3
            else
                echo -e "${RED}Please install Homebrew first: https://brew.sh${NC}"
                exit 1
            fi
        fi
        echo -e "${GREEN}Python3 installed: $(python3 --version)${NC}"
    fi
}

# Install Docker
install_docker() {
    if command_exists docker; then
        echo -e "${GREEN}Docker is already installed: $(docker --version)${NC}"
        return
    fi

    echo "Installing Docker..."
    if [[ "$OS" == "linux" ]]; then
        # Install Docker using official script
        curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
        sudo sh /tmp/get-docker.sh
        rm /tmp/get-docker.sh

        # Add current user to docker group
        sudo usermod -aG docker "$USER"
        echo -e "${YELLOW}You may need to log out and back in for Docker group membership to take effect.${NC}"
    elif [[ "$OS" == "macos" ]]; then
        echo -e "${YELLOW}Please install Docker Desktop for Mac from: https://www.docker.com/products/docker-desktop${NC}"
        echo "After installation, this script will continue with other tools."
        read -p "Press enter to continue after installing Docker Desktop..."
    fi

    if command_exists docker; then
        echo -e "${GREEN}Docker installed: $(docker --version)${NC}"
    fi
}

# Install Docker Compose
install_docker_compose() {
    if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
        echo -e "${GREEN}Docker Compose is already installed${NC}"
        return
    fi

    echo "Installing Docker Compose..."
    if [[ "$OS" == "linux" ]]; then
        sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo -e "${GREEN}Docker Compose installed: $(docker-compose --version)${NC}"
    elif [[ "$OS" == "macos" ]]; then
        echo -e "${GREEN}Docker Compose is included with Docker Desktop${NC}"
    fi
}

# Install GitHub CLI
install_github_cli() {
    if command_exists gh; then
        echo -e "${GREEN}GitHub CLI is already installed: $(gh --version | head -n1)${NC}"
        return
    fi

    echo "Installing GitHub CLI..."
    if [[ "$OS" == "linux" ]]; then
        type -p curl >/dev/null || sudo apt install curl -y
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        sudo apt update
        sudo apt install gh -y
    elif [[ "$OS" == "macos" ]]; then
        if command_exists brew; then
            brew install gh
        else
            echo -e "${RED}Please install Homebrew first: https://brew.sh${NC}"
            exit 1
        fi
    fi

    echo -e "${GREEN}GitHub CLI installed: $(gh --version | head -n1)${NC}"
}

# Install pre-commit
install_pre_commit() {
    if command_exists pre-commit; then
        echo -e "${GREEN}pre-commit is already installed: $(pre-commit --version)${NC}"
        return
    fi

    echo "Installing pre-commit..."
    if command_exists pip3; then
        pip3 install --user pre-commit
    elif command_exists pip; then
        pip install --user pre-commit
    else
        echo -e "${RED}pip not found. Please install Python first.${NC}"
        exit 1
    fi

    # Make sure pip user bin is in PATH
    if [[ "$OS" == "linux" ]]; then
        export PATH="$HOME/.local/bin:$PATH"
    elif [[ "$OS" == "macos" ]]; then
        export PATH="$HOME/Library/Python/$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)/bin:$PATH"
    fi

    echo -e "${GREEN}pre-commit installed: $(pre-commit --version)${NC}"
}

# Main installation flow
main() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Bootstrap Development Environment${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""

    install_python
    install_terraform
    install_docker
    install_docker_compose
    install_github_cli
    install_pre_commit

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Installation Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run 'pre-commit install' to set up pre-commit hooks"
    echo "2. See CONTRIBUTING.md for development guidelines"
    echo ""

    if [[ "$OS" == "linux" ]] && groups | grep -q docker; then
        :
    elif [[ "$OS" == "linux" ]]; then
        echo -e "${YELLOW}Note: You may need to log out and back in for Docker group membership to take effect.${NC}"
    fi
}

main "$@"
