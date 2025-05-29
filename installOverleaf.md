# Install Overleaf Toolkit: A Beginner's Guide

Welcome to this step-by-step guide for installing the Overleaf Toolkit on your system. Overleaf is an online LaTeX editor that allows you to create, edit, and collaborate on LaTeX documents easily. This guide is designed for beginners with little to no experience with Docker or command-line tools. Follow each step carefully, and by the end, you'll have your own local Overleaf instance running.

## What You’ll Need
- A computer running Linux (this guide is tailored for Linux systems).
- Internet access to download necessary tools and files.
- Basic familiarity with using a terminal (don’t worry, I’ll explain each command).

## Step-by-Step Installation Instructions

### Step 1: Open a Terminal
- On your Linux system, open a terminal. This is where you’ll type all the commands. You can usually find it by searching for "Terminal" in your applications menu.

### Step 2: Update Your System
- Before installing anything, it’s good practice to update your system’s package list to ensure you get the latest versions of software.
- Type the following command and press Enter:
  ```
  sudo apt update
  ```
- You might be prompted to enter your password. This command updates the list of available packages on your system.

### Step 3: Install Git (if not already installed)
- Git is a tool used to download the Overleaf Toolkit code from the internet.
- Check if Git is installed by typing:
  ```
  git --version
  ```
- If you see a version number, it’s installed. If not, install it with:
  ```
  sudo apt install -y git
  ```

### Step 4: Install Python Tools (for compatibility)
- Some tools require Python components. Install them by typing:
  ```
  sudo apt install -y python3-setuptools python3-pip
  ```
- This ensures there are no compatibility issues later.

### Step 5: Install Docker Compose
- Docker Compose is a tool for managing multiple Docker containers, which Overleaf uses to run.
- Check if it’s installed:
  ```
  docker-compose --version
  ```
- If it’s not installed, install it via apt:
  ```
  sudo apt install -y docker-compose
  ```
- If that doesn’t work, try installing via pip:
  ```
  sudo pip3 install docker-compose
  ```
- If you’re using a newer version of Docker, you might need to use `docker compose` (note the space) instead of `docker-compose`. Check with:
  ```
  docker compose version
  ```

### Step 6: Clone the Overleaf Toolkit Repository
- Now, download the Overleaf Toolkit code. Type:
  ```
  git clone https://github.com/overleaf/toolkit.git overleaf-toolkit
  ```
- This creates a folder named `overleaf-toolkit` in your current directory with all the necessary files.

### Step 7: Navigate to the Overleaf Toolkit Directory
- Move into the folder you just created:
  ```
  cd overleaf-toolkit
  ```
- All following commands will be run from inside this directory.

### Step 8: Initialize Configuration
- Set up the configuration files for Overleaf by running:
  ```
  bin/init
  ```
- This creates a `config` folder with necessary settings. If the folder already exists, this step will be skipped.

### Step 9: Start Overleaf Containers
- Now, start the Overleaf services. This might take a while as it downloads and sets up Docker containers.
- Run:
  ```
  bin/up
  ```
- If this fails, try with sudo:
  ```
  sudo bin/up
  ```
- If `bin/up` doesn’t work due to Docker Compose not being recognized, try:
  ```
  docker compose up
  ```
- Or with sudo:
  ```
  sudo docker compose up
  ```
- You should see log output indicating the containers are starting. Press `CTRL-C` to stop watching the logs, but the containers will keep running if you used `bin/start` instead of `bin/up`.

### Step 10: Create Your First Admin Account
- Open a web browser and go to:
  ```
  http://localhost/launchpad
  ```
- You’ll see a form to register. Enter an email and password of your choice for the admin account and click "Register".
- Then, go to:
  ```
  http://localhost/login
  ```
- Enter the credentials you just set and log in. You’ll be taken to a welcome page.

### Step 11: Start Using Overleaf
- After logging in, click the green button at the bottom of the welcome page to start using Overleaf.
- Go to:
  ```
  http://localhost/project
  ```
- Click the button to create your first project and follow the instructions to start editing LaTeX documents.

### Step 12: Stopping the Overleaf Containers (Optional)
- When you’re done, you can stop the Overleaf services by running:
  ```
  bin/down
  ```
- Or with sudo if needed:
  ```
  sudo bin/down
  ```

## Troubleshooting Tips
- If something doesn’t work, run the doctor tool to diagnose issues:
  ```
  bin/doctor
  ```
- Check the logs for errors:
  ```
  bin/logs -f web
  ```

## Q&A for Beginners

**Q: What is Overleaf, and why should I install it locally?**  
A: Overleaf is an online LaTeX editor for creating professional documents like research papers or theses. Installing it locally with the Overleaf Toolkit allows you to use it offline or customize it, and it’s free with the Community Edition.

**Q: I get an error saying Docker is not installed. What do I do?**  
A: Docker is required to run Overleaf. Install Docker first by following instructions at https://docs.docker.com/get-docker/. Then retry the steps from Step 5.

**Q: How do I know if the Overleaf containers are running?**  
A: After running `bin/up`, you can check the logs with `bin/logs`. If you see activity or no error messages, it’s likely running. Also, accessing http://localhost/launchpad in your browser should show the registration page if it’s up.

**Q: I forgot the admin credentials I set. How can I reset them?**  
A: If you forget your credentials, you may need to reset the Overleaf data. Stop the containers with `bin/down`, remove the data folder with caution (e.g., `rm -rf data`), and reinitialize with `bin/init` then `bin/up`. You’ll start fresh and can set new credentials.

**Q: Can I use Overleaf Toolkit on Windows or Mac?**  
A: Yes, but this guide is for Linux. The process is similar on Windows or Mac, but you’ll need Docker Desktop installed, and some commands might differ. Check the official Overleaf Toolkit documentation in the `doc` folder for platform-specific notes.

**Q: What if I encounter other errors or need help?**  
A: Run `bin/doctor` to diagnose issues. For Community Edition users, open an issue on GitHub at https://github.com/overleaf/toolkit/issues. Include the output of `bin/doctor` in your request for help.

Congratulations! You’ve installed Overleaf locally. Start creating amazing LaTeX documents now!
