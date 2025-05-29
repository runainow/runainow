#!/bin/bash

# Script to install Overleaf Toolkit on a Linux system
# This script assumes Docker and Docker Compose are already installed

echo "Starting Overleaf Toolkit installation..."

# Update package list
echo "Updating package list..."
sudo apt update

# Install git if not already installed
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    sudo apt install -y git
else
    echo "git is already installed."
fi

# Install python3-setuptools and python3-pip for compatibility
echo "Installing python3-setuptools and python3-pip for compatibility..."
sudo apt install -y python3-setuptools python3-pip

# Clone Overleaf Toolkit repository if not already cloned
if [ ! -d "overleaf-toolkit" ]; then
    echo "Cloning Overleaf Toolkit repository..."
    git clone https://github.com/overleaf/toolkit.git overleaf-toolkit
else
    echo "Overleaf Toolkit repository already cloned."
fi

# Navigate to the toolkit directory
cd overleaf-toolkit

# Initialize configuration only if config files do not exist
if [ ! -d "config" ]; then
    echo "Initializing Overleaf Toolkit configuration..."
    bin/init
else
    echo "Configuration already exists, skipping initialization."
fi

# Start Overleaf containers, try docker compose if docker-compose fails
echo "Starting Overleaf containers (this may take a while)..."
if command -v docker-compose &> /dev/null; then
    bin/up
    if [ $? -ne 0 ]; then
        echo "docker-compose failed, trying with sudo..."
        sudo bin/up
    fi
else
    echo "docker-compose not found, trying docker compose (newer version)..."
    if command -v docker &> /dev/null; then
        docker compose up
        if [ $? -ne 0 ]; then
            echo "docker compose failed, trying with sudo..."
            sudo docker compose up
        fi
    else
        echo "Neither docker-compose nor docker compose found. Please ensure Docker is installed and configured correctly."
        echo "You can run 'install_docker.sh' to install Docker if needed."
        exit 1
    fi
fi

echo "Overleaf Toolkit installation complete."
echo "Overleaf should now be accessible at http://localhost/launchpad to create your admin account."
echo "After registering, log in at http://localhost/login."
echo "Use 'bin/down' in the overleaf-toolkit directory to stop the containers."
