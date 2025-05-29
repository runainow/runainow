#!/bin/bash

# Script to verify Overleaf Toolkit installation and status
# This script checks if Overleaf is installed and running correctly

echo "Verifying Overleaf Toolkit installation..."

# Check if overleaf-toolkit directory exists
if [ ! -d "overleaf-toolkit" ]; then
    echo "Error: Overleaf Toolkit directory not found. Please run 'install_overleaf.sh' first."
    exit 1
fi

# Navigate to the toolkit directory
cd overleaf-toolkit

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please run 'install_docker.sh' to install Docker."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please run 'install_docker.sh' to install Docker Compose."
    exit 1
fi

# Run the doctor tool to diagnose installation issues
echo "Running Overleaf Doctor to check installation..."
bin/doctor

# Check container status
echo "Checking status of Overleaf containers..."
if command -v docker-compose &> /dev/null; then
    bin/docker-compose ps
    if [ $? -ne 0 ]; then
        echo "docker-compose ps failed, trying with sudo..."
        sudo bin/docker-compose ps
    fi
else
    docker compose ps
    if [ $? -ne 0 ]; then
        echo "docker compose ps failed, trying with sudo..."
        sudo docker compose ps
    fi
fi

# Check logs for recent activity (last 10 lines for brevity)
echo "Checking recent logs for Overleaf web service..."
bin/logs -f web | tail -n 10

# Provide instructions for further verification
echo "Verification steps complete."
echo "1. Check the output of 'bin/doctor' above for any warnings or errors."
echo "2. Ensure the container status shows services as 'Up' or running."
echo "3. Open a browser and go to http://localhost/launchpad to see if the registration page loads."
echo "If you encounter issues, refer to the logs or run 'bin/logs -f web' for detailed output."
echo "You can also start the containers if they are not running by using 'bin/up' or 'sudo bin/up' in the overleaf-toolkit directory."
