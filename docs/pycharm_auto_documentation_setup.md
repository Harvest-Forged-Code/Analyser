# PyCharm Automatic Documentation Update Setup

This document explains how to configure PyCharm to automatically update documentation (PDF, UML diagrams, flowcharts, README.md) whenever code is changed and the run button is pressed.

## Overview

The setup consists of:
1. A script that updates documentation
2. PyCharm external tool configuration
3. PyCharm run configuration setup

When properly configured, pressing the run button in PyCharm will:
1. Automatically update the documentation PDF
2. Regenerate all UML diagrams
3. Update the README.md file with content from the documentation
4. Run the application

## Documentation Update Script

A script has been created at `scripts/update_documentation.sh` that handles:
- Compiling LaTeX documents to PDF
- Generating images from PlantUML files
- Updating the README.md file with content from the LaTeX documentation
- Ensuring all documentation is up-to-date

The script has been tested and works correctly.

## PyCharm Configuration Steps

### 1. Set Up External Tool

1. Open PyCharm preferences/settings
   - macOS: PyCharm → Preferences
   - Windows/Linux: File → Settings

2. Navigate to Tools → External Tools

3. Click the + button to add a new external tool

4. Configure the external tool with these settings:
   - Name: `Update Documentation`
   - Program: `/Users/Prabhukumar/Projects/PycharmProjects/Analyser/scripts/update_documentation.sh`
   - Working directory: `$ProjectFileDir$`
   - Check "Synchronize files after execution"

5. Click OK to save the external tool

### 2. Create Compound Run Configuration

1. Click on the run configuration dropdown in the toolbar and select "Edit Configurations..."

2. Click the + button and select "Compound"

3. Name the configuration "Run with Documentation Update"

4. In the "Configurations" section, click the + button to add configurations:
   - First, add the "Update Documentation" external tool
   - Then, add your main application run configuration (e.g., "app")

5. Make sure "Run with Documentation Update" is set as the default configuration

6. Click OK to save the configuration

### 3. Test the Configuration

1. Make a small change to your code

2. Press the run button (or use Shift+F10)

3. Verify that:
   - The documentation update script runs
   - The PDF documentation is updated
   - The UML diagrams are regenerated
   - The README.md file is updated with content from the documentation
   - The application runs normally

## Troubleshooting

If the automatic documentation update doesn't work:

1. Check that the script has execute permissions:
   ```
   chmod +x /Users/Prabhukumar/Projects/PycharmProjects/Analyser/scripts/update_documentation.sh
   ```

2. Verify that all required tools are installed:
   - LaTeX (pdflatex)
   - Java
   - PlantUML JAR

3. Run the script manually to check for errors:
   ```
   /Users/Prabhukumar/Projects/PycharmProjects/Analyser/scripts/update_documentation.sh
   ```

4. Check the PyCharm event log for any error messages

## Maintenance

If you need to modify the documentation update process:

1. Edit the script at `scripts/update_documentation.sh`

2. If you add new UML diagrams, they will be automatically processed if they are placed in the `docs/uml/` directory with the `.puml` extension

3. If you change the LaTeX file name or location, update the script accordingly

## Benefits

This setup ensures that:
1. Documentation is always up-to-date with the latest code changes
2. UML diagrams accurately reflect the current system architecture
3. The README.md file is always in sync with the full documentation
4. GitHub Pages (which uses the README.md) always has current information
5. Developers don't need to remember to update documentation manually
6. The PDF documentation is always ready for distribution

## Related Documentation

For more information about the README update process, see [README Update Process](readme_update_process.md).