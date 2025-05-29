# Installing Docker TeX Live with VSCode

This guide provides step-by-step instructions to set up a Docker container with TeX Live for LaTeX document processing using Visual Studio Code (VSCode). By using Docker, you can avoid installing LaTeX directly on your system and work in a consistent, isolated environment.

## Prerequisites

Before starting, ensure you have the following installed on your system:
- **Docker**: A container platform to run TeX Live. Download and install from [Docker's official website](https://www.docker.com/get-started).
- **VSCode**: A lightweight code editor. Download from [VSCode's official website](https://code.visualstudio.com/).
- **Docker Extension for VSCode** (optional but recommended): This extension integrates Docker with VSCode for easier container management. Install it from the VSCode Marketplace.

## Step 1: Install Docker

1. **Download Docker**: Visit [Docker Desktop](https://www.docker.com/products/docker-desktop) and download the version suitable for your operating system (Windows, macOS, or Linux).
2. **Install Docker**: Follow the installation instructions provided on the website. For Linux, you might need to use terminal commands (e.g., `sudo apt install docker.io` for Ubuntu).
3. **Verify Installation**: Open a terminal or command prompt and run:
   ```
   docker --version
   ```
   You should see the Docker version information if the installation was successful.
4. **Start Docker**: Ensure the Docker daemon is running. On Windows or macOS, Docker Desktop should start automatically after installation. On Linux, you might need to run:
   ```
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

## Step 2: Pull the TeX Live Docker Image

TeX Live is available as a Docker image that you can pull from Docker Hub.

1. Open a terminal or command prompt.
2. Run the following command to download the latest TeX Live image:
   ```
   docker pull texlive/texlive:latest
   ```
   This might take a few minutes depending on your internet speed, as the image is quite large (several GB).

## Step 3: Set Up a Project Directory

Create a directory on your local machine where you will store your LaTeX files. This directory will be mounted to the Docker container so that files are accessible both inside and outside the container.

1. Create a new folder, for example, `latex_project`, in a convenient location.
2. Open this folder in VSCode by selecting `File > Open Folder...` and choosing the folder.

## Step 4: Create a Script to Run the TeX Live Container

To simplify running the Docker container, create a shell script that will start the container with the correct settings.

1. In VSCode, create a new file named `run_texlive_container.sh` in your project directory.
2. Add the following content to the script:
   ```bash
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
   ```
3. Save the file.
4. Make the script executable (on Linux or macOS) by running the following command in the terminal:
   ```
   chmod +x run_texlive_container.sh
   ```

## Step 5: Run the TeX Live Container

1. In VSCode, open the integrated terminal (`Ctrl + ~` or `View > Terminal`).
2. Run the script to start the container:
   ```
   ./run_texlive_container.sh
   ```
   If you're on Windows and using Git Bash or another shell, you might need to adjust the command or run it with `bash run_texlive_container.sh`.
3. If prompted for a password (when using `sudo`), enter your system password.
4. You should now be inside a bash shell in the Docker container, with your project directory mounted at `/workdir`. You can verify this by running:
   ```
   ls
   ```
   You should see the files in your project directory.

## Step 6: Test LaTeX Compilation

To ensure everything is set up correctly, create and compile a simple LaTeX document.

1. While inside the container, create a test file named `testLatex.tex` using a text editor like `nano` (available in the container):
   ```
   nano testLatex.tex
   ```
2. Paste the following content into the file:
   ```latex
   \documentclass{article}
   \title{Test Document}
   \author{Your Name}
   \date{}
   \begin{document}
   \maketitle
   \section{Introduction}
   This is a test document to verify that LaTeX is working correctly in the Docker container.
   \end{document}
   ```
3. Save and exit the editor (in `nano`, press `Ctrl+O`, `Enter`, then `Ctrl+X`).
4. Compile the document using `pdflatex`:
   ```
   pdflatex testLatex.tex
   ```
5. If successful, you should see output indicating that `testLatex.pdf` was created. You can verify this by running:
   ```
   ls
   ```
   You should see `testLatex.pdf` in the list.

## Step 7: Exit the Container

Since the container was started with the `--rm` flag, it will be automatically removed when you exit the bash session.

1. Type `exit` or press `Ctrl+D` to exit the container shell.
   ```
   exit
   ```

## Step 8: View the Compiled PDF

The compiled PDF (`testLatex.pdf`) is saved in your project directory on your local machine because of the mounted volume. You can open it with any PDF viewer, or in VSCode if you have a PDF viewer extension installed.

## Step 9: Managing Docker via VSCode

To manage Docker containers and images directly within VSCode, you can use the Docker extension, which provides a graphical interface for Docker operations. This can simplify tasks like starting, stopping, and inspecting containers without using the terminal for every action.

### Install the Docker Extension

1. Open VSCode.
2. Go to the Extensions view by clicking on the Extensions icon in the Activity Bar on the side of the window or by pressing `Ctrl+Shift+X`.
3. Search for "Docker" in the Extensions view search box.
4. Find the extension named "Docker" by Microsoft and click `Install`. This extension allows you to manage Docker images, containers, and more directly from VSCode.

### Set Up the Docker Extension

1. After installation, ensure that Docker is running on your system. The extension will automatically detect the Docker daemon if it's active.
2. You might see a Docker icon appear in the Activity Bar. Click on it to open the Docker view. If you don't see the icon, you can access the Docker view from the Command Palette (`Ctrl+Shift+P`) by typing "Docker".

### Using the Docker Extension to Manage Containers

1. **View Docker Images**: In the Docker view, expand the "Images" section to see all Docker images available on your system, including `texlive/texlive:latest` if you've pulled it.
2. **Run a Container**: Right-click on the `texlive/texlive:latest` image and select "Run" or "Run Interactive" to start a new container. You can specify volume mounts and working directories in the run configuration if needed. For an interactive shell similar to the `run_texlive_container.sh` script:
   - Choose "Run Interactive".
   - VSCode will open a terminal pane connected to the container's bash shell.
3. **View Running Containers**: Expand the "Containers" section in the Docker view to see all active containers. You can right-click on a container to stop, restart, or remove it.
4. **Inspect Containers and Images**: Right-click on any container or image to inspect its details, view logs, or attach a shell to a running container.
5. **Compile LaTeX Files**: While the Docker extension doesn't directly compile LaTeX files, you can attach to a running container or start a new one, then use the integrated terminal in VSCode to run commands like `pdflatex testLatex.tex`.

### Creating Custom Tasks for Automation

You can set up custom tasks in VSCode to automate running Docker commands for LaTeX compilation without manually starting a container each time.

1. In VSCode, go to `Terminal > Configure Tasks...` or press `Ctrl+Shift+P` and type "Tasks: Configure Task".
2. Select "Create tasks.json file from template" and choose "Others" to create a custom task.
3. Replace the content of `tasks.json` in the `.vscode` folder with something like:
   ```json
   {
       "version": "2.0.0",
       "tasks": [
           {
               "label": "Compile LaTeX with Docker",
               "type": "shell",
               "command": "docker run --rm -v \"$(pwd)\":/workdir -w /workdir texlive/texlive:latest pdflatex ${fileBasename}",
               "group": {
                   "kind": "build",
                   "isDefault": true
               },
               "problemMatcher": []
           }
       ]
   }
   ```
4. Save the file. Now, when you open a LaTeX file, you can press `Ctrl+Shift+B` (default build shortcut) to run the task, which will compile the current file using Docker. Adjust the command if you need `sudo` or if your user isn't in the Docker group yet.

### Benefits of Using the Docker Extension

- **Graphical Interface**: Manage containers and images without terminal commands.
- **Integration**: Seamlessly switch between coding and container management within VSCode.
- **Customization**: Define custom commands or tasks for frequent operations like compiling LaTeX files.

### Notes

- If your user is not yet in the Docker group (as set up earlier), you might still need to prepend `sudo` to commands run via tasks or the extension, or ensure you've logged out and back in after adding your user to the group.
- For complex LaTeX projects requiring multiple compilation steps (e.g., BibTeX), you might still need to use an interactive container session or define more detailed tasks.

By using the Docker extension in VSCode, you can streamline your workflow for managing Docker containers running TeX Live, making it easier to focus on writing and compiling LaTeX documents.

## Additional Tips

- **Reusing the Container**: Each time you run `./run_texlive_container.sh`, a new container instance is created. If you want to keep a container running for multiple sessions, remove the `--rm` flag from the script, but remember to manually remove the container later using `docker rm <container_id>`.
- **VSCode Integration**: Install the "LaTeX Workshop" extension in VSCode for syntax highlighting and other LaTeX editing features. However, compilation will still need to be done inside the Docker container.
- **Large Projects**: For larger LaTeX projects, ensure your project directory structure is organized, as all files will be accessible within the container at `/workdir`.

## Troubleshooting

- **Permission Denied Error**: If you encounter permission issues when running Docker, ensure you have the necessary permissions. On Linux, you might need to add your user to the `docker` group:
  ```
  sudo usermod -aG docker $USER
  ```
  Then log out and log back in for the change to take effect.
- **Image Pull Fails**: Ensure you have an active internet connection when pulling the `texlive/texlive:latest` image.
- **Compilation Errors**: If `pdflatex` fails, check the error messages in the terminal for clues. Common issues include syntax errors in the LaTeX code or missing packages (though the `texlive/texlive:latest` image includes a full TeX Live installation).

By following these steps, you should have a fully functional TeX Live environment running in a Docker container, accessible through VSCode for all your LaTeX document needs.
