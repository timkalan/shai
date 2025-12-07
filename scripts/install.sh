#!/bin/sh
#
# shai - Installer Script
#
# This script downloads the correct binary from GitHub Releases
# and installs it to /usr/local/bin.
#
# Usage: curl -fsSL https://github.com/timkalan/shai/raw/main/scripts/install.sh | sh
#

set -e # Exit on any error

REPO="timkalan/shai"
# Attempt to fetch the latest version from GitHub API
LATEST_VERSION=$(curl -s https://api.github.com/repos/$REPO/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')

if [ -z "$LATEST_VERSION" ]; then
  echo "Warning: Could not fetch latest version from GitHub. Falling back to default."
  VERSION="v0.1.0" 
else
  VERSION="$LATEST_VERSION"
fi

INSTALL_DIR="/usr/local/bin"
BINARY_NAME="shai"
TARGET_FILE="$INSTALL_DIR/$BINARY_NAME"

# Detect OS and Architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case $OS in
  linux) OS_NAME="linux" ;;
  darwin) OS_NAME="macos" ;;
  *)
    echo "Error: Unsupported OS '$OS'" >&2
    exit 1
    ;;
esac

case $ARCH in
  x86_64) ARCH_NAME="x64" ;;
  aarch64 | arm64) ARCH_NAME="arm64" ;;
  *)
    echo "Error: Unsupported architecture '$ARCH'" >&2
    exit 1
    ;;
esac

# Construct Download URL
RELEASE_BINARY_NAME="shai-${OS_NAME}-${ARCH_NAME}"
DOWNLOAD_URL="https://github.com/$REPO/releases/download/$VERSION/$RELEASE_BINARY_NAME"

# Download Binary
echo "Downloading shai ($RELEASE_BINARY_NAME)..."
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$DOWNLOAD_URL" -o "/tmp/$BINARY_NAME"
elif command -v wget >/dev/null 2>&1; then
  wget -qO "/tmp/$BINARY_NAME" "$DOWNLOAD_URL"
else
  echo "Error: You need either curl or wget to install shai." >&2
  exit 1
fi

# Install Binary
echo "Installing to $INSTALL_DIR..."
chmod +x "/tmp/$BINARY_NAME"

# Use sudo if $INSTALL_DIR is not writable by the current user
if [ ! -w "$INSTALL_DIR" ]; then
  echo "sudo password may be required to install to $INSTALL_DIR"
  sudo mv "/tmp/$BINARY_NAME" "$TARGET_FILE"
else
  mv "/tmp/$BINARY_NAME" "$TARGET_FILE"
fi

# Print Next Steps
echo ""
echo "✅ shai was installed successfully to $TARGET_FILE"
echo ""
echo "--- IMPORTANT: Next Steps ---"
echo ""
echo "shai requires a Google AI API key to function."
echo "1. Get your key from Google AI Studio."
echo "2. Add the key to your shell's startup file (e.g., ~/.zshrc)."
echo ""
echo "   # Add these two lines to ~/.zshrc:"
echo "   export GOOGLE_GENERATIVE_AI_API_KEY=\"YOUR_API_KEY_GOES_HERE\""
echo "   eval \"\$(shai --zsh-init)\""
echo ""
echo "3. Restart your shell or run: source ~/.zshrc"
