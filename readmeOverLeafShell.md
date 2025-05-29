# README for Overleaf Installation Shell Scripts

This document provides an overview and usage instructions for a set of shell scripts designed to simplify the installation and verification of the Overleaf Toolkit on a Linux system. These scripts automate the process, making it accessible even for beginners with minimal command-line experience.

## Overview of Scripts

This collection includes three shell scripts, each serving a specific purpose in the setup of a local Overleaf instance:

1. **install_docker.sh** - Installs Docker and Docker Compose, which are essential prerequisites for running the Overleaf Toolkit.
2. **install_overleaf.sh** - Installs the Overleaf Toolkit by cloning the repository, initializing configuration, and starting the Overleaf containers.
3. **verify_overleaf_install.sh** - Verifies the installation of Overleaf by checking the status of Docker containers and running diagnostic tools to ensure everything is set up correctly.

## Prerequisites

- A Linux system (these scripts are tailored for Ubuntu/Debian-based distributions).
- Internet access to download necessary software and repositories.
- Basic terminal access (you just need to be able to run commands in a terminal).

## How to Use These Scripts

Follow these steps in order to set up Overleaf locally. Each script should be run from the same directory where they are located.

### Step 1: Make the Scripts Executable
Before running the scripts, you need to make them executable. Open a terminal in the directory containing the scripts and run:
```
chmod +x install_docker.sh install_overleaf.sh verify_overleaf_install.sh
```
This command grants permission to execute the scripts.

### Step 2: Install Docker
Run the first script to install Docker and Docker Compose:
```
./install_docker.sh
```
- **What it does**: Updates your system, installs Docker Engine and Docker Compose, and automatically adds your user to the Docker group to grant permission to run Docker commands without sudo.
- **Note**: After installation, you must log out and log back in (or restart your system) for the Docker group permission to take effect. You can test Docker with `docker run hello-world` once logged back in. This script uses `sudo` for system updates and installations, so you will likely be prompted to enter your sudo password.

### Step 3: Install Overleaf Toolkit
Once Docker is installed, run the second script to install Overleaf:
```
./install_overleaf.sh
```
- **What it does**: Updates your system, installs necessary tools like Git, clones the Overleaf Toolkit repository, initializes configuration, and starts the Overleaf containers.
- **Note**: This process may take a while as it downloads and sets up Docker containers. After completion, Overleaf should be accessible at `http://localhost/launchpad` for account registration. This script uses `sudo` for some commands and may prompt for your sudo password if initial attempts fail.

### Step 4: Verify Installation
Finally, run the verification script to ensure everything is working correctly:
```
./verify_overleaf_install.sh
```
- **What it does**: Checks if Docker and Overleaf Toolkit are installed, runs the Overleaf Doctor tool for diagnostics, displays container status, and shows recent logs for the web service.
- **Note**: Review the output for any errors or warnings. The script also provides instructions to check if Overleaf is accessible in your browser. This script may prompt for your sudo password if it needs to run Docker commands with elevated privileges.

## After Installation
- **Access Overleaf**: Open a browser and go to `http://localhost/launchpad` to create your admin account. Then log in at `http://localhost/login`.
- **Create Projects**: After logging in, navigate to `http://localhost/project` to start creating LaTeX documents.
- **Stopping Overleaf**: To stop the Overleaf containers, navigate to the `overleaf-toolkit` directory and run `bin/down` or `sudo bin/down`.

## Troubleshooting
- If a script fails, read the error messages in the terminal output for clues. Common issues include missing permissions or internet connectivity problems.
- **Sudo Password Prompts**: The scripts use `sudo` for certain commands (e.g., system updates, installations, and Docker operations). You will likely be prompted to enter your sudo password unless your system is configured to run sudo commands without a password.
- Use the `verify_overleaf_install.sh` script to diagnose issues after installation.
- For detailed logs, run `bin/logs -f web` in the `overleaf-toolkit` directory.
- If Docker permissions are an issue, ensure you've logged out and back in after running `install_docker.sh`.

## Additional Resources
- Refer to `installOverleaf.md` for a detailed step-by-step guide on installing Overleaf manually.
- Visit the Overleaf Toolkit GitHub page at `https://github.com/overleaf/toolkit` for more documentation and community support.

By using these scripts, setting up a local Overleaf instance becomes a straightforward process. If you encounter any issues not covered here, feel free to seek help from the Overleaf community or documentation.
