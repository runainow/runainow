#!/bin/bash
# This script runs a Docker container with TeX Live Full, mounting the current directory
# to allow working on LaTeX files within the container.

# Ensure the user is in the docker group or use sudo
if groups | grep -q docker; then
    DOCKER_CMD="docker"
else
    DOCKER_CMD="sudo docker"
fi

# Run the container with the current directory mounted
$DOCKER_CMD run -it --rm -v "$(pwd)":/workdir -w /workdir texlive/texlive:latest bash
