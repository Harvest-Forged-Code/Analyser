#!/bin/bash
#
# Budget Analyser - macOS Gatekeeper Bypass Script
#
# This script removes the quarantine attribute from the Budget Analyser app,
# allowing it to open without the Gatekeeper warning:
# "Apple could not verify 'Budget Analyser.app' is free of malware..."
#
# Usage:
#   ./scripts/open_macos_app.sh [path_to_app]
#
# Examples:
#   ./scripts/open_macos_app.sh                              # Uses default path
#   ./scripts/open_macos_app.sh "/Applications/Budget Analyser.app"
#   ./scripts/open_macos_app.sh ~/Downloads/Budget\ Analyser.app
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default app paths to check
DEFAULT_PATHS=(
    "/Applications/Budget Analyser.app"
    "$HOME/Applications/Budget Analyser.app"
    "$HOME/Downloads/Budget Analyser.app"
    "$(dirname "$0")/../dist/Budget Analyser.app"
)

print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Budget Analyser - Gatekeeper Bypass${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

show_help() {
    echo "Usage: $0 [path_to_app]"
    echo ""
    echo "Removes the macOS quarantine attribute from Budget Analyser.app"
    echo "to bypass the Gatekeeper warning for unsigned apps."
    echo ""
    echo "Arguments:"
    echo "  path_to_app    Path to Budget Analyser.app (optional)"
    echo ""
    echo "If no path is provided, the script will search in:"
    echo "  - /Applications/Budget Analyser.app"
    echo "  - ~/Applications/Budget Analyser.app"
    echo "  - ~/Downloads/Budget Analyser.app"
    echo "  - ./dist/Budget Analyser.app"
    echo ""
    echo "Examples:"
    echo "  $0"
    echo "  $0 \"/Applications/Budget Analyser.app\""
    echo "  $0 ~/Downloads/Budget\\ Analyser.app"
    exit 0
}

find_app() {
    # If path provided as argument, use it
    if [[ -n "$1" ]]; then
        if [[ -d "$1" ]]; then
            echo "$1"
            return 0
        else
            return 1
        fi
    fi
    
    # Search default paths
    for path in "${DEFAULT_PATHS[@]}"; do
        # Expand the path
        expanded_path=$(eval echo "$path")
        if [[ -d "$expanded_path" ]]; then
            echo "$expanded_path"
            return 0
        fi
    done
    
    return 1
}

# Main script
print_header

# Check for help flag
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_help
fi

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    print_error "This script must be run on macOS"
    exit 1
fi

# Find the app
APP_PATH=$(find_app "$1") || {
    print_error "Budget Analyser.app not found!"
    echo ""
    if [[ -n "$1" ]]; then
        print_info "The specified path does not exist: $1"
    else
        print_info "Searched in:"
        for path in "${DEFAULT_PATHS[@]}"; do
            echo "    - $path"
        done
    fi
    echo ""
    print_info "Please provide the correct path:"
    echo "    $0 \"/path/to/Budget Analyser.app\""
    exit 1
}

print_success "Found app at: $APP_PATH"

# Check if quarantine attribute exists
if xattr "$APP_PATH" 2>/dev/null | grep -q "com.apple.quarantine"; then
    print_info "Quarantine attribute detected"
    
    # Remove quarantine attribute
    print_info "Removing quarantine attribute..."
    xattr -d com.apple.quarantine "$APP_PATH"
    
    print_success "Quarantine attribute removed successfully!"
else
    print_warning "No quarantine attribute found (app may already be cleared)"
fi

# Ask if user wants to open the app
echo ""
read -p "Would you like to open Budget Analyser now? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Opening Budget Analyser..."
    open "$APP_PATH"
    print_success "App launched!"
else
    print_info "You can open the app manually by double-clicking it or running:"
    echo "    open \"$APP_PATH\""
fi

echo ""
print_success "Done! The app should now open without Gatekeeper warnings."
echo ""
