#!/bin/bash

# Script to install Docker on a Linux system (Ubuntu/Debian based)
# This script automates the installation of Docker and Docker Compose

echo "Starting Docker installation..."

# Update package list
echo "Updating package list..."
sudo apt update

# Install prerequisites
echo "Installing prerequisites for Docker..."
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker’s official GPG key
echo "Adding Docker's GPG key..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the stable repository
echo "Setting up Docker repository..."
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package list again with Docker repo
sudo apt update

# Install Docker Engine
echo "Installing Docker Engine..."
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Verify Docker installation
if command -v docker &> /dev/null; then
    echo "Docker installed successfully!"
    docker --version
else
    echo "Docker installation failed. Please check for errors above."
    exit 1
fi

# Install Docker Compose
echo "Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/v2.17.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify Docker Compose installation
if command -v docker-compose &> /dev/null; then
    echo "Docker Compose installed successfully!"
    docker-compose --version
else
    echo "Docker Compose installation failed. Falling back to pip installation..."
    sudo apt install -y python3-pip
    sudo pip3 install docker-compose
    if command -v docker-compose &> /dev/null; then
        echo "Docker Compose installed via pip successfully!"
        docker-compose --version
    else
        echo "Docker Compose installation failed. Please check for errors above."
        exit 1
    fi
fi

# Add user to docker group to run docker without sudo (optional, requires logout/login)
echo "Adding current user to docker group (you may need to log out and log back in)..."
sudo usermod -aG docker $USER

echo "Docker and Docker Compose installation complete. Please log out and log back in if you encounter permission issues."
echo "You can test Docker with 'docker run hello-world' after logging back in."
