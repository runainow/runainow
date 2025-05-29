# Compilation Guide for sn01.tex

This document provides instructions for compiling the LaTeX file `sn01.tex` into a PDF, including processing the bibliography to ensure all references are correctly included in the output document.

## Overview

The provided shell script `compile_sn01.sh` automates the process of compiling the LaTeX document `sn01.tex` into a PDF. It handles the necessary steps to process the bibliography using BibTeX and runs the LaTeX compiler multiple times to resolve all references and cross-references.

## Prerequisites

- **TeX Live**: Ensure that TeX Live (or a similar LaTeX distribution) is installed on your system. This includes tools like `pdflatex` and `bibtex`, which are essential for compiling LaTeX documents and processing bibliographies.
- **Linux/Unix Environment**: The script is designed to run in a Linux or Unix-like environment (e.g., Ubuntu, macOS with bash). If you're on Windows, you might need to use a subsystem like WSL (Windows Subsystem for Linux) or adjust the script accordingly.

## Files Included

- `sn01.tex`: The main LaTeX source file for the document.
- `sn01.bib`: The bibliography file containing reference entries.
- `bst/sn-mathphys-num.bst`: The bibliography style file required for formatting references in the Springer journal style.
- `compile_sn01.sh`: The shell script to automate the compilation process.

## How to Use the Compilation Script

Follow these steps to compile `sn01.tex` into a PDF:

1. **Navigate to the Correct Directory**:
   Open a terminal and change to the `sn1` directory where `sn01.tex` is located. Use the command:
   ```
   cd /path/to/latex1/sn1
   ```
   Replace `/path/to/latex1` with the actual path to the parent directory on your system.

2. **Make the Script Executable**:
   Ensure the shell script has execute permissions. Run the following command:
   ```
   chmod +x compile_sn01.sh
   ```

3. **Run the Compilation Script**:
   Execute the script to start the compilation process. You can use either of the following commands:
   ```
   ./compile_sn01.sh
   ```
   or
   ```
   bash compile_sn01.sh
   ```

4. **Check the Output**:
   The script will perform the following actions:
   - Check if `sn01.tex` is present in the current directory to ensure it's run from the correct location.
   - Copy the bibliography style file `sn-mathphys-num.bst` to the current directory if it's not already there.
   - Run `pdflatex sn01.tex` for the initial compilation.
   - Run `bibtex sn01` to process the bibliography.
   - Run `pdflatex sn01.tex` twice more to incorporate the bibliography and finalize all references.
   After successful execution, the output PDF file `sn01.pdf` will be updated in the `sn1` directory.

## Troubleshooting

- **Error: sn01.tex not found**: Ensure you are running the script from the `sn1` directory where `sn01.tex` is located.
- **BibTeX Errors**: If BibTeX fails to find the style file even after copying, verify that `bst/sn-mathphys-num.bst` exists in the `bst` subdirectory.
- **Undefined References**: If references still appear as `??` in the PDF, it might be due to mismatched citation keys between `sn01.tex` and `sn01.bib`. Check the LaTeX source for correct citation commands.
- **LaTeX Warnings**: The compilation output may show warnings about font substitutions or undefined references. These are often non-critical but can be addressed by reviewing the LaTeX source code if necessary.

## Manual Compilation (Optional)

If you prefer to compile the document manually without using the script, follow these steps in the `sn1` directory:

1. Copy the bibliography style file:
   ```
   cp bst/sn-mathphys-num.bst .
   ```
2. Run the initial LaTeX compilation:
   ```
   pdflatex sn01.tex
   ```
3. Process the bibliography:
   ```
   bibtex sn01
   ```
4. Run LaTeX compilation twice more to resolve references:
   ```
   pdflatex sn01.tex
   pdflatex sn01.tex
   ```

The resulting `sn01.pdf` will be created or updated in the current directory.

## Notes

- The script runs `pdflatex` multiple times because LaTeX often requires multiple passes to resolve all cross-references and bibliography entries.
- Ensure that all necessary files (`sn01.tex`, `sn01.bib`, and the style file) are present and correctly formatted to avoid compilation errors.

If you encounter persistent issues, consult the log files (`sn01.log` for LaTeX errors, `sn01.blg` for BibTeX errors) for detailed error messages.