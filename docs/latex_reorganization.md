# LaTeX Files Reorganization

## Overview

This document describes the reorganization of LaTeX-related files in the documentation directory.

## Changes Made

### 1. Created a New LaTeX Directory

A new directory `docs/LaTeX` was created to store all LaTeX-related files.

### 2. Moved LaTeX Files

The following LaTeX-related files were moved from the root documentation directory to the new LaTeX directory:

- `budget_analyser_documentation.aux`
- `budget_analyser_documentation.log`
- `budget_analyser_documentation.out`
- `budget_analyser_documentation.tex`
- `budget_analyser_documentation.toc`

### 3. Kept PDF Files in Root Directory

The PDF file `budget_analyser_documentation.pdf` was kept in the root documentation directory for easy access.

## Benefits

1. **Improved Organization**: LaTeX source files and auxiliary files are now separated from the final PDF documents.
2. **Cleaner Documentation Directory**: The root documentation directory is now cleaner and focuses on the final documents.
3. **Better Maintainability**: LaTeX-related files are grouped together, making it easier to maintain and update them.

## Accessing LaTeX Files

To access the LaTeX source files for editing:
- Navigate to the `docs/LaTeX` directory
- Edit the `.tex` files as needed
- Compile the LaTeX documents to generate updated PDF files in the root documentation directory

## Next Steps

No further action is needed. The documentation directory is now organized with:
- LaTeX source and auxiliary files in the `docs/LaTeX` directory
- PDF files in the root documentation directory