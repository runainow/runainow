 LaTeX Editor with PDF Preview & TikZ Graphics
A powerful, web-based LaTeX editor built with Streamlit that provides real-time PDF compilation, TikZ graphics support, and comprehensive error handling.

![LaTeX Editor](https://img.shields.io/badge/LaTeX-Editor-blue?style=for-the-badge&

🚀 Quick Operations
📋⚡ One-Click Paste & Compile: Instantly paste TikZ code from clipboard and compile

🎨⚡ Quick TikZ Test: Fast testing of current TikZ code

🧪 Test Error Function: Generate test errors for debugging

📄 Main LaTeX Editor
Full LaTeX document editing with syntax highlighting

Real-time PDF compilation and preview

Download compiled PDFs

Comprehensive error handling and display

🖼️ TikZ Graphics Support
Dedicated TikZ code editor

Standalone TikZ compilation for quick testing

Extensive TikZ library support (positioning, shapes, arrows, decorations, patterns, calc)

Live preview of TikZ graphics

📋 Clipboard Integration
Read TikZ code directly from system clipboard

Apply clipboard content to editors

Manual input option for TikZ code

🚨 Advanced Error Handling
Persistent error message display

Copy error messages to clipboard (first 30 lines)

Separate error tracking for different compilation types

Clear and detailed error reporting

📚 Template Library
Quick TikZ templates (Basic Nodes, Flowcharts, Math Functions)

Pre-built examples and code snippets

Easy template loading

🛠️ Installation
Prerequisites
Python 3.8 or higher

LaTeX distribution (TeXLive, MiKTeX, etc.)

pdflatex command available in PATH

Dependencies Installation
Using uv (recommended):

bash
uv add streamlit pdf2image pillow pyperclip
Using pip:

bash
pip install streamlit pdf2image pillow pyperclip
LaTeX Dependencies
Ensure you have a complete LaTeX installation with TikZ support:

Ubuntu/Debian:

bash
sudo apt update
sudo apt install texlive-full
macOS (with Homebrew):

bash
brew install --cask mactex
Windows:

Download and install MiKTeX or TeX Live

🚀 Usage
Running the Application
bash
streamlit run latex_web_editor.py
The application will open in your default web browser at http://localhost:8501

Basic Workflow
Edit LaTeX Code: Use the main editor (left column) for complete LaTeX documents

Test TikZ Graphics: Use the TikZ editor (middle column) for quick graphics testing

Use Clipboard Features: Copy TikZ code and use one-click paste functionality

Compile and Preview: Generate PDFs with real-time preview

Handle Errors: View detailed error messages and copy them for debugging

Quick Operations Guide
One-Click Paste & Compile
Copy TikZ code to your system clipboard

Click "📋⚡ One-Click Paste & Compile"

The code will be automatically pasted, compiled, and previewed

Template Usage
Navigate to the "Clipboard Functions" section

Select a template from the dropdown

Click "📝 Load Template"

Apply the template to your editor

📁 Project Structure
text
latex-editor/
├── latex_web_editor.py          # Main application file
├── README.md                    # This file
└── requirements.txt             # Python dependencies
🔧 Configuration
Default LaTeX Template
The editor comes with a pre-configured LaTeX template including:

Standard article document class

UTF-8 encoding support

AMS Math packages

TikZ with common libraries

Geometry package for layout

TikZ Libraries Included
positioning - Advanced node positioning

shapes - Additional node shapes

arrows - Arrow styles and decorations

decorations.markings - Path decorations

patterns - Fill patterns

calc - Coordinate calculations

🐛 Troubleshooting
Common Issues
"pdflatex command not found"

Ensure LaTeX is installed and pdflatex is in your system PATH

Try running pdflatex --version in terminal to verify installation

"Need to install pyperclip"

Install the package: uv add pyperclip or pip install pyperclip

Compilation errors not showing

Check the "🚨 Error Messages" section at the top of the page

Use the copy error buttons to get detailed error information

PDF preview not displaying

Ensure pdf2image is installed: uv add pdf2image

On some systems, you may need to install poppler-utils

Error Message Locations
Error messages are displayed in multiple locations:

🚨 Error Messages Section (top of page) - Persistent error display

Individual column status - Shows error count and status

Copy error buttons - Available in each section for error extraction

🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

Development Setup
Clone the repository

Install dependencies: uv install or pip install -r requirements.txt

Run the application: streamlit run latex_web_editor.py

📄 License
This project is open source and available under the MIT License.

🙏 Acknowledgments
Built with Streamlit

LaTeX compilation via pdflatex

PDF processing with pdf2image

Clipboard integration with pyperclip

📞 Support
If you encounter any issues or have questions:

Check the troubleshooting section above

Use the "🧪 Test Error Function" to verify error handling

Copy error messages using the provided buttons for easier debugging

Create an issue with detailed error information

Happy LaTeX editing! 📝✨
