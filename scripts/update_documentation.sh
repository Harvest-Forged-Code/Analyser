#!/bin/bash

# Script to update documentation (PDF, UML diagrams, flowcharts)
# This script is automatically run by PyCharm when the run button is pressed

# Set the base directory to the project root
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Base directory: $BASE_DIR"

# Set the paths for documentation
LATEX_DIR="$BASE_DIR/docs/LaTeX"
UML_DIR="$BASE_DIR/docs/uml"
PDF_OUTPUT_DIR="$BASE_DIR/docs"

# Set the path for the PlantUML JAR
PLANTUML_JAR="/Users/Prabhukumar/Library/Application Support/JetBrains/PyCharm2025.1/plugins/plantuml4idea/lib/plantuml-mit-1.2025.4.jar"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if required tools are installed
if ! command_exists pdflatex; then
    echo "Error: pdflatex is not installed. Please install LaTeX."
    exit 1
fi

if ! command_exists java; then
    echo "Error: java is not installed. Please install Java."
    exit 1
fi

if [ ! -f "$PLANTUML_JAR" ]; then
    echo "Error: PlantUML JAR not found at $PLANTUML_JAR"
    exit 1
fi

echo "All required tools are installed."

# Update LaTeX documentation
echo "Updating LaTeX documentation..."
cd "$LATEX_DIR" || exit 1
pdflatex -interaction=nonstopmode budget_analyser_documentation.tex
pdflatex -interaction=nonstopmode budget_analyser_documentation.tex  # Run twice for references
mv budget_analyser_documentation.pdf "$PDF_OUTPUT_DIR/"
echo "LaTeX documentation updated."

# Update UML diagrams
echo "Updating UML diagrams..."
cd "$UML_DIR" || exit 1
for puml_file in *.puml; do
    echo "Processing $puml_file..."
    java -jar "$PLANTUML_JAR" "$puml_file"
done
echo "UML diagrams updated."

# Update README.md with content from the documentation
echo "Updating README.md..."
cd "$BASE_DIR" || exit 1

# Check if Python is installed
if ! command_exists python3; then
    echo "Error: python3 is not installed. Please install Python 3."
    exit 1
fi

# Check if the update_readme.py script exists
README_SCRIPT="$BASE_DIR/scripts/update_readme.py"
if [ ! -f "$README_SCRIPT" ]; then
    echo "Error: update_readme.py script not found at $README_SCRIPT"
    exit 1
fi

# Make the script executable if it's not already
chmod +x "$README_SCRIPT"

# Run the script to update the README.md
python3 "$README_SCRIPT"
if [ $? -ne 0 ]; then
    echo "Error: Failed to update README.md"
    exit 1
fi
echo "README.md updated."

echo "Documentation update completed successfully."