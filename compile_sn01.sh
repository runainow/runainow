#!/bin/bash

# Script to compile sn01.tex into PDF with bibliography processing
# Run this script from the sn1 directory

# Ensure the script is run from the correct directory
if [ ! -f "sn01.tex" ]; then
    echo "Error: sn01.tex not found. Please run this script from the sn1 directory."
    exit 1
fi

# Copy the bibliography style file to the current directory if not already present
if [ ! -f "sn-mathphys-num.bst" ]; then
    cp bst/sn-mathphys-num.bst .
    echo "Copied sn-mathphys-num.bst to current directory."
fi

# Compile the LaTeX file with bibliography
echo "Running pdflatex for initial compilation..."
pdflatex sn01.tex

echo "Processing bibliography with bibtex..."
bibtex sn01

echo "Running pdflatex to incorporate bibliography..."
pdflatex sn01.tex

echo "Running pdflatex again to finalize references..."
pdflatex sn01.tex

echo "Compilation complete. Output file: sn01.pdf"