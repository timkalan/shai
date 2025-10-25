#!/bin/sh
#
# shai - Installer Script
#
# This script downloads the correct binary from GitHub Releases
# and installs it to /usr/local/bin.
#
# Usage: curl -fsSL https://github.com/timkalan/shai/raw/main/install.sh | sh
#

set -e # Exit on any error

# --- START: Customizeable Variables ---
REPO="timkalan/shai"
VERSION="v0.1.0" # Make sure this matches your GitHub Release tag
# --- END: Customizeable Variables ---

INSTALL_DIR="/usr/local/bin"
BINARY_NAME="shai"
TARGET_FILE="$INSTALL_DIR/$BINARY_NAME"

# 1. Detect OS and Architecture
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

# 2. Construct Download URL
RELEASE_BINARY_NAME="shai-${OS_NAME}-${ARCH_NAME}"
DOWNLOAD_URL="https://github.com/$REPO/releases/download/$VERSION/$RELEASE_BINARY_NAME"

# 3. Download Binary
echo "Downloading shai ($RELEASE_BINARY_NAME)..."
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$DOWNLOAD_URL" -o "/tmp/$BINARY_NAME"
elif command -v wget >/dev/null 2>&1; then
  wget -qO "/tmp/$BINARY_NAME" "$DOWNLOAD_URL"
else
  echo "Error: You need either curl or wget to install shai." >&2
  exit 1
fi

# 4. Install Binary
echo "Installing to $INSTALL_DIR..."
chmod +x "/tmp/$BINARY_NAME"

# Use sudo if $INSTALL_DIR is not writable by the current user
if [ ! -w "$INSTALL_DIR" ]; then
  echo "sudo password may be required to install to $INSTALL_DIR"
  sudo mv "/tmp/$BINARY_NAME" "$TARGET_FILE"
else
  mv "/tmp/$BINARY_NAME" "$TARGET_FILE"
fi

# 5. Print Next Steps
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
echo "   export GOOGLE_API_KEY=\"YOUR_API_KEY_GOES_HERE\""
echo "   eval \"\$(shai --zsh-init)\""
echo ""
echo "3. Restart your shell or run: source ~/.zshrc"
