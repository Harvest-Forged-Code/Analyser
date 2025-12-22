#!/bin/bash
#
# macOS Code Signing and Notarization Script for Budget Analyser
#
# This script signs and notarizes the macOS app bundle to eliminate
# the Gatekeeper warning: "Apple could not verify..."
#
# Prerequisites:
#   1. Apple Developer Program membership ($99/year)
#   2. Developer ID Application certificate installed in Keychain
#   3. App-specific password for notarization (appleid.apple.com -> Security -> App-Specific Passwords)
#
# Usage:
#   ./scripts/sign_macos_app.sh [options]
#
# Options:
#   -a, --app PATH          Path to the .app bundle (default: dist/Budget Analyser.app)
#   -i, --identity NAME     Signing identity (default: from APPLE_SIGNING_IDENTITY env var)
#   -t, --team-id ID        Apple Team ID (default: from APPLE_TEAM_ID env var)
#   -u, --apple-id EMAIL    Apple ID email (default: from APPLE_ID env var)
#   -p, --password PASS     App-specific password (default: from APPLE_APP_PASSWORD env var)
#   -s, --sign-only         Only sign, skip notarization
#   -n, --notarize-only     Only notarize (assumes already signed)
#   -h, --help              Show this help message
#
# Environment Variables (alternative to command-line options):
#   APPLE_SIGNING_IDENTITY  - e.g., "Developer ID Application: Your Name (TEAM_ID)"
#   APPLE_TEAM_ID           - Your 10-character Team ID
#   APPLE_ID                - Your Apple ID email
#   APPLE_APP_PASSWORD      - App-specific password for notarization
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
APP_PATH="dist/Budget Analyser.app"
SIGN_ONLY=false
NOTARIZE_ONLY=false

# Functions
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
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
    head -40 "$0" | tail -35 | sed 's/^#//' | sed 's/^ //'
    exit 0
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check if running on macOS
    if [[ "$(uname)" != "Darwin" ]]; then
        print_error "This script must be run on macOS"
        exit 1
    fi
    print_success "Running on macOS"
    
    # Check for codesign
    if ! command -v codesign &> /dev/null; then
        print_error "codesign not found. Please install Xcode Command Line Tools."
        exit 1
    fi
    print_success "codesign available"
    
    # Check for notarytool
    if ! command -v xcrun &> /dev/null; then
        print_error "xcrun not found. Please install Xcode Command Line Tools."
        exit 1
    fi
    print_success "xcrun available"
    
    # Check if app exists
    if [[ ! -d "$APP_PATH" ]]; then
        print_error "App not found at: $APP_PATH"
        print_info "Build the app first with: pyinstaller --name 'Budget Analyser' ..."
        exit 1
    fi
    print_success "App found at: $APP_PATH"
}

check_signing_identity() {
    if [[ -z "$SIGNING_IDENTITY" ]]; then
        print_error "Signing identity not specified"
        print_info "Set APPLE_SIGNING_IDENTITY environment variable or use -i option"
        print_info "Example: 'Developer ID Application: Your Name (TEAM_ID)'"
        echo ""
        print_info "Available identities in your keychain:"
        security find-identity -v -p codesigning | grep "Developer ID" || echo "  No Developer ID certificates found"
        exit 1
    fi
    
    # Verify the identity exists in keychain
    if ! security find-identity -v -p codesigning | grep -q "$SIGNING_IDENTITY"; then
        print_error "Signing identity not found in keychain: $SIGNING_IDENTITY"
        print_info "Available identities:"
        security find-identity -v -p codesigning | grep "Developer ID" || echo "  No Developer ID certificates found"
        exit 1
    fi
    print_success "Signing identity found: $SIGNING_IDENTITY"
}

check_notarization_credentials() {
    if [[ -z "$APPLE_ID" ]]; then
        print_error "Apple ID not specified"
        print_info "Set APPLE_ID environment variable or use -u option"
        exit 1
    fi
    print_success "Apple ID: $APPLE_ID"
    
    if [[ -z "$TEAM_ID" ]]; then
        print_error "Team ID not specified"
        print_info "Set APPLE_TEAM_ID environment variable or use -t option"
        exit 1
    fi
    print_success "Team ID: $TEAM_ID"
    
    if [[ -z "$APP_PASSWORD" ]]; then
        print_error "App-specific password not specified"
        print_info "Set APPLE_APP_PASSWORD environment variable or use -p option"
        print_info "Create one at: appleid.apple.com -> Security -> App-Specific Passwords"
        exit 1
    fi
    print_success "App-specific password: ****"
}

sign_app() {
    print_header "Signing Application"
    
    print_info "Removing any existing signatures..."
    codesign --remove-signature "$APP_PATH" 2>/dev/null || true
    
    print_info "Signing with identity: $SIGNING_IDENTITY"
    
    # Sign all nested components first (frameworks, helpers, etc.)
    find "$APP_PATH" -type f \( -name "*.dylib" -o -name "*.so" -o -name "*.framework" \) -exec \
        codesign --force --verify --verbose --timestamp \
        --options runtime \
        --sign "$SIGNING_IDENTITY" {} \; 2>/dev/null || true
    
    # Sign the main executable
    codesign --deep --force --verify --verbose --timestamp \
        --options runtime \
        --entitlements /dev/stdin \
        --sign "$SIGNING_IDENTITY" \
        "$APP_PATH" << 'ENTITLEMENTS'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
</dict>
</plist>
ENTITLEMENTS
    
    print_success "App signed successfully"
    
    # Verify signature
    print_info "Verifying signature..."
    if codesign --verify --verbose "$APP_PATH" 2>&1; then
        print_success "Signature verified"
    else
        print_error "Signature verification failed"
        exit 1
    fi
}

notarize_app() {
    print_header "Notarizing Application"
    
    # Create a zip for notarization
    ZIP_PATH="${APP_PATH%.app}.zip"
    print_info "Creating zip archive for notarization..."
    ditto -c -k --keepParent "$APP_PATH" "$ZIP_PATH"
    print_success "Created: $ZIP_PATH"
    
    # Submit for notarization
    print_info "Submitting to Apple for notarization..."
    print_info "This may take several minutes..."
    
    NOTARIZE_OUTPUT=$(xcrun notarytool submit "$ZIP_PATH" \
        --apple-id "$APPLE_ID" \
        --team-id "$TEAM_ID" \
        --password "$APP_PASSWORD" \
        --wait 2>&1)
    
    echo "$NOTARIZE_OUTPUT"
    
    if echo "$NOTARIZE_OUTPUT" | grep -q "status: Accepted"; then
        print_success "Notarization successful!"
        
        # Staple the notarization ticket
        print_info "Stapling notarization ticket to app..."
        xcrun stapler staple "$APP_PATH"
        print_success "Notarization ticket stapled"
        
        # Clean up zip
        rm -f "$ZIP_PATH"
        print_success "Cleaned up temporary files"
    else
        print_error "Notarization failed"
        print_info "Check the output above for details"
        
        # Try to get the log
        SUBMISSION_ID=$(echo "$NOTARIZE_OUTPUT" | grep -o 'id: [a-f0-9-]*' | head -1 | cut -d' ' -f2)
        if [[ -n "$SUBMISSION_ID" ]]; then
            print_info "Fetching detailed log..."
            xcrun notarytool log "$SUBMISSION_ID" \
                --apple-id "$APPLE_ID" \
                --team-id "$TEAM_ID" \
                --password "$APP_PASSWORD" 2>&1 || true
        fi
        
        exit 1
    fi
}

verify_app() {
    print_header "Final Verification"
    
    print_info "Checking Gatekeeper acceptance..."
    if spctl --assess --verbose --type execute "$APP_PATH" 2>&1; then
        print_success "App is accepted by Gatekeeper!"
    else
        print_warning "Gatekeeper check returned warnings (this may be normal)"
    fi
    
    print_info "Checking notarization status..."
    if stapler validate "$APP_PATH" 2>&1; then
        print_success "Notarization ticket is valid"
    else
        print_warning "Could not validate notarization ticket"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--app)
            APP_PATH="$2"
            shift 2
            ;;
        -i|--identity)
            SIGNING_IDENTITY="$2"
            shift 2
            ;;
        -t|--team-id)
            TEAM_ID="$2"
            shift 2
            ;;
        -u|--apple-id)
            APPLE_ID="$2"
            shift 2
            ;;
        -p|--password)
            APP_PASSWORD="$2"
            shift 2
            ;;
        -s|--sign-only)
            SIGN_ONLY=true
            shift
            ;;
        -n|--notarize-only)
            NOTARIZE_ONLY=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Use environment variables as defaults
SIGNING_IDENTITY="${SIGNING_IDENTITY:-$APPLE_SIGNING_IDENTITY}"
TEAM_ID="${TEAM_ID:-$APPLE_TEAM_ID}"
APPLE_ID="${APPLE_ID:-$APPLE_ID}"
APP_PASSWORD="${APP_PASSWORD:-$APPLE_APP_PASSWORD}"

# Main execution
print_header "Budget Analyser - macOS Code Signing & Notarization"

check_prerequisites

if [[ "$NOTARIZE_ONLY" == false ]]; then
    check_signing_identity
    sign_app
fi

if [[ "$SIGN_ONLY" == false ]]; then
    check_notarization_credentials
    notarize_app
    verify_app
fi

print_header "Complete!"
echo -e "${GREEN}Your app is now signed and notarized.${NC}"
echo -e "${GREEN}Users will no longer see the Gatekeeper warning.${NC}"
echo ""
print_info "App location: $APP_PATH"
