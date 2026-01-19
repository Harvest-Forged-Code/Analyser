#!/usr/bin/env python3
"""
Script to extract content from LaTeX documentation and update the README.md file.
This script is called by update_documentation.sh after generating the PDF documentation.
"""

import re
import os
import sys
from datetime import datetime

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LATEX_FILE = os.path.join(BASE_DIR, "documentation", "LaTeX", "budget_analyser_documentation.tex")
README_FILE = os.path.join(BASE_DIR, "README.md")

def read_latex_file(file_path):
    """Read the LaTeX file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading LaTeX file: {e}")
        sys.exit(1)

def extract_section(content, section_name):
    """Extract a specific section from the LaTeX content"""
    pattern = rf"\\section{{{section_name}}}\n(.*?)(?=\\section{{|\\chapter{{|\\end{{document}})"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_subsection(content, subsection_name):
    """Extract a specific subsection from the LaTeX content"""
    pattern = rf"\\subsection{{{subsection_name}}}\n(.*?)(?=\\subsection{{|\\section{{|\\chapter{{|\\end{{document}})"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_chapter(content, chapter_name):
    """Extract a specific chapter from the LaTeX content"""
    pattern = rf"\\chapter{{{chapter_name}}}\n(.*?)(?=\\chapter{{|\\end{{document}})"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_all_subsections(content, section_name):
    """Extract all subsections from a specific section"""
    section_content = extract_section(content, section_name)
    if not section_content:
        return {}
    
    # Find all subsection names in the section
    subsection_names = re.findall(r'\\subsection{(.*?)}', section_content, re.DOTALL)
    
    # Extract content for each subsection
    subsections = {}
    for name in subsection_names:
        subsection_content = extract_subsection(section_content, name)
        subsections[name] = subsection_content
    
    return subsections

def convert_latex_to_markdown(latex_content):
    """Convert LaTeX formatting to Markdown"""
    if not latex_content:
        return ""
        
    # Replace LaTeX itemize environment with Markdown bullet points
    latex_content = re.sub(r'\\begin{itemize}(.*?)\\end{itemize}', 
                          lambda m: convert_itemize(m.group(1)), 
                          latex_content, flags=re.DOTALL)
    
    # Replace LaTeX enumerate environment with Markdown numbered list
    latex_content = re.sub(r'\\begin{enumerate}(.*?)\\end{enumerate}', 
                          lambda m: convert_enumerate(m.group(1)), 
                          latex_content, flags=re.DOTALL)
    
    # Replace LaTeX lstlisting environment with Markdown code blocks
    latex_content = re.sub(r'\\begin{lstlisting}(.*?)\\end{lstlisting}', 
                          lambda m: f"```\n{m.group(1).strip()}\n```", 
                          latex_content, flags=re.DOTALL)
    
    # Remove LaTeX section and subsection commands (we'll handle these separately)
    latex_content = re.sub(r'\\subsection{.*?}', '', latex_content)
    latex_content = re.sub(r'\\section{.*?}', '', latex_content)
    
    # Replace LaTeX bold text with Markdown bold
    latex_content = re.sub(r'\\textbf{(.*?)}', r'**\1**', latex_content)
    
    # Replace LaTeX italic text with Markdown italic
    latex_content = re.sub(r'\\textit{(.*?)}', r'*\1*', latex_content)
    
    # Replace LaTeX code with Markdown code
    latex_content = re.sub(r'\\texttt{(.*?)}', r'`\1`', latex_content)
    
    # Remove LaTeX comments
    latex_content = re.sub(r'%.*?\n', '\n', latex_content)
    
    # Replace LaTeX item commands with Markdown list items
    latex_content = re.sub(r'\\item\s+(.*?)(?=\\item|$)', r'- \1\n', latex_content, flags=re.DOTALL)
    
    # Remove remaining LaTeX commands that don't have a Markdown equivalent
    latex_content = re.sub(r'\\[a-zA-Z]+(\[.*?\])?{', '{', latex_content)
    latex_content = re.sub(r'\\[a-zA-Z]+', '', latex_content)
    
    # Clean up extra whitespace
    latex_content = re.sub(r'\n\s*\n\s*\n', '\n\n', latex_content)
    
    # Clean up any remaining LaTeX artifacts
    latex_content = re.sub(r'{(.*?)}', r'\1', latex_content)
    
    # Clean up any remaining backslashes
    latex_content = latex_content.replace('\\', '')
    
    # Trim whitespace
    latex_content = latex_content.strip()
    
    return latex_content

def convert_itemize(itemize_content):
    """Convert LaTeX itemize environment to Markdown bullet points"""
    # Extract each \item and convert to Markdown bullet point
    items = re.findall(r'\\item\s+(.*?)(?=\\item|$)', itemize_content, re.DOTALL)
    markdown_list = ""
    for item in items:
        # Clean up the item content
        item = item.strip()
        # Add as a Markdown bullet point
        markdown_list += f"- {item}\n"
    return markdown_list

def convert_enumerate(enumerate_content):
    """Convert LaTeX enumerate environment to Markdown numbered list"""
    # Extract each \item and convert to Markdown numbered list item
    items = re.findall(r'\\item\s+(.*?)(?=\\item|$)', enumerate_content, re.DOTALL)
    markdown_list = ""
    for i, item in enumerate(items, 1):
        # Clean up the item content
        item = item.strip()
        # Add as a Markdown numbered list item
        markdown_list += f"{i}. {item}\n"
    return markdown_list

def generate_readme_content(latex_content):
    """Generate the README.md content from the LaTeX content"""
    # Extract the title
    title_match = re.search(r'\\title{.*?{\\Huge\\bfseries\s+(.*?)}\\\\\s*\\vspace', latex_content, re.DOTALL)
    title = title_match.group(1) if title_match else "Budget Analyser"
    
    # Extract chapters we want to include
    introduction = extract_chapter(latex_content, "Introduction")
    architecture = extract_chapter(latex_content, "System Architecture")
    components = extract_chapter(latex_content, "Components")
    functionality = extract_chapter(latex_content, "Functionality")
    installation = extract_chapter(latex_content, "Installation and Setup")
    usage = extract_chapter(latex_content, "Usage Guide")
    
    # Extract sections from Introduction chapter
    overview = extract_section(introduction, "Overview")
    purpose = extract_section(introduction, "Purpose")
    target_audience = extract_section(introduction, "Target Audience")
    
    # If target_audience is empty, extract it directly from the LaTeX content
    if not target_audience:
        target_audience_pattern = r'\\section{Target Audience}.*?\\begin{itemize}(.*?)\\end{itemize}'
        target_audience_match = re.search(target_audience_pattern, introduction, re.DOTALL)
        if target_audience_match:
            target_audience = f"\\begin{{itemize}}{target_audience_match.group(1)}\\end{{itemize}}"
    
    # Extract sections from System Architecture chapter
    arch_overview = extract_section(architecture, "Overview")
    
    # For architectural layers, we'll extract the content and the subsections separately
    arch_layers = extract_section(architecture, "Architectural Layers")
    
    # Extract subsections from the Architectural Layers section
    view_layer = re.search(r'\\subsection{View Layer}(.*?)(?=\\subsection{|\\section{|\\chapter{|$)', architecture, re.DOTALL)
    model_layer = re.search(r'\\subsection{Model Layer}(.*?)(?=\\subsection{|\\section{|\\chapter{|$)', architecture, re.DOTALL)
    controller_layer = re.search(r'\\subsection{Controller Layer}(.*?)(?=\\subsection{|\\section{|\\chapter{|$)', architecture, re.DOTALL)
    framework_layer = re.search(r'\\subsection{Framework Layer}(.*?)(?=\\subsection{|\\section{|\\chapter{|$)', architecture, re.DOTALL)
    
    # Extract sections from Functionality chapter
    key_features = extract_section(functionality, "Key Features")
    
    # If key_features is empty, extract it directly from the LaTeX content
    if not key_features:
        key_features_pattern = r'\\section{Key Features}.*?\\subsection{(.*?)}(.*?)(?=\\section{|\\chapter{|$)'
        key_features_match = re.search(key_features_pattern, functionality, re.DOTALL)
        if key_features_match:
            key_features = key_features_match.group(2)
    
    # Extract sections from Installation chapter
    prerequisites = extract_section(installation, "Prerequisites")
    installation_steps = extract_section(installation, "Installation Steps")
    running = extract_section(installation, "Running the Application")
    
    # If running is empty, extract it directly from the LaTeX content
    if not running:
        running_pattern = r'\\section{Running the Application}(.*?)(?=\\section{|\\chapter{|$)'
        running_match = re.search(running_pattern, installation, re.DOTALL)
        if running_match:
            running = running_match.group(1)
    
    # Extract subsections from Usage Guide chapter
    logging_in = extract_section(usage, "Logging In")
    navigating = extract_section(usage, "Navigating the Dashboard")
    viewing_reports = extract_section(usage, "Viewing Reports")
    uploading = extract_section(usage, "Uploading Statements")
    
    # If uploading is empty, extract it directly from the LaTeX content
    if not uploading:
        uploading_pattern = r'\\section{Uploading Statements}(.*?)(?=\\section{|\\chapter{|$)'
        uploading_match = re.search(uploading_pattern, usage, re.DOTALL)
        if uploading_match:
            uploading = uploading_match.group(1)
    
    # Convert LaTeX to Markdown
    overview_md = convert_latex_to_markdown(overview)
    purpose_md = convert_latex_to_markdown(purpose)
    target_audience_md = convert_latex_to_markdown(target_audience)
    arch_overview_md = convert_latex_to_markdown(arch_overview)
    
    # Convert architectural layers subsections to Markdown
    view_layer_md = convert_latex_to_markdown(view_layer.group(1) if view_layer else "")
    model_layer_md = convert_latex_to_markdown(model_layer.group(1) if model_layer else "")
    controller_layer_md = convert_latex_to_markdown(controller_layer.group(1) if controller_layer else "")
    framework_layer_md = convert_latex_to_markdown(framework_layer.group(1) if framework_layer else "")
    
    key_features_md = convert_latex_to_markdown(key_features)
    prerequisites_md = convert_latex_to_markdown(prerequisites)
    installation_steps_md = convert_latex_to_markdown(installation_steps)
    running_md = convert_latex_to_markdown(running)
    logging_in_md = convert_latex_to_markdown(logging_in)
    navigating_md = convert_latex_to_markdown(navigating)
    viewing_reports_md = convert_latex_to_markdown(viewing_reports)
    uploading_md = convert_latex_to_markdown(uploading)
    
    # Build the README content
    readme_content = f"""# {title}

## Introduction

### Overview
{overview_md}

### Purpose
{purpose_md}

### Target Audience
{target_audience_md}

## System Architecture
{arch_overview_md}

### Architectural Layers

#### View Layer
{view_layer_md}

#### Model Layer
{model_layer_md}

#### Controller Layer
{controller_layer_md}

#### Framework Layer
{framework_layer_md}

## Key Features
{key_features_md}

## Installation and Setup

### Prerequisites
{prerequisites_md}

### Installation Steps
{installation_steps_md}

### Running the Application
{running_md}

## Usage Guide

### Logging In
{logging_in_md}

### Navigating the Dashboard
{navigating_md}

### Viewing Reports
{viewing_reports_md}

### Uploading Statements
{uploading_md}

---

*This README is automatically generated from the comprehensive documentation. For more details, please refer to the [full documentation](docs/budget_analyser_documentation.pdf).*

*Last updated: {datetime.now().strftime('%Y-%m-%d')}*
"""
    return readme_content

def update_readme(readme_content):
    """Update the README.md file with the generated content"""
    try:
        with open(README_FILE, 'w', encoding='utf-8') as file:
            file.write(readme_content)
        print(f"README.md updated successfully at {README_FILE}")
        return True
    except Exception as e:
        print(f"Error updating README.md: {e}")
        return False

def main():
    """Main function to extract content and update README.md"""
    print("Starting README.md update process...")
    
    # Read the LaTeX file
    latex_content = read_latex_file(LATEX_FILE)
    
    # Generate the README content
    readme_content = generate_readme_content(latex_content)
    
    # Update the README.md file
    success = update_readme(readme_content)
    
    if success:
        print("README.md update completed successfully.")
    else:
        print("README.md update failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()