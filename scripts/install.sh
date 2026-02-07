#!/bin/sh
#
# shai - Installer Script
#
# Usage: curl -fsSL https://github.com/timkalan/shai/raw/main/scripts/install.sh | sh
#

set -e # Exit on any error

REPO="timkalan/shai"

# Fetch Version
echo "Checking latest version..."
LATEST_VERSION=$(curl -s https://api.github.com/repos/$REPO/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')

if [ -z "$LATEST_VERSION" ]; then
	echo "Error: Could not fetch latest version from GitHub."
	echo "Please check your internet connection or try again later."
	echo "You can also manually download from: https://github.com/$REPO/releases"
	exit 1
fi

VERSION="$LATEST_VERSION"

INSTALL_DIR="/usr/local/bin"
BINARY_NAME="shai"
TARGET_FILE="$INSTALL_DIR/$BINARY_NAME"

# Detect OS/Arch
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

RELEASE_BINARY_NAME="shai-${OS_NAME}-${ARCH_NAME}"
DOWNLOAD_URL="https://github.com/$REPO/releases/download/$VERSION/$RELEASE_BINARY_NAME"

# Download
echo "Downloading $RELEASE_BINARY_NAME from $VERSION..."

# Check if the URL is valid (HEAD request) before trying to download
if curl --output /dev/null --silent --head --fail "$DOWNLOAD_URL"; then
	# URL exists
	:
else
	echo "Error: The release binary '$RELEASE_BINARY_NAME' was not found at:"
	echo "$DOWNLOAD_URL"
	exit 1
fi

if command -v curl >/dev/null 2>&1; then
	curl -L --progress-bar "$DOWNLOAD_URL" -o "/tmp/$BINARY_NAME"
elif command -v wget >/dev/null 2>&1; then
	wget -q --show-progress -O "/tmp/$BINARY_NAME" "$DOWNLOAD_URL"
else
	echo "Error: You need curl or wget." >&2
	exit 1
fi

# Install
echo "Installing to $INSTALL_DIR..."
chmod +x "/tmp/$BINARY_NAME"

if [ ! -w "$INSTALL_DIR" ]; then
	echo "Sudo permissions required to move binary to $INSTALL_DIR"

	if [ -t 0 ]; then
		sudo mv "/tmp/$BINARY_NAME" "$TARGET_FILE"
	else
		# If not running in a terminal (piped), try to open /dev/tty
		sudo mv "/tmp/$BINARY_NAME" "$TARGET_FILE" </dev/tty
	fi
else
	mv "/tmp/$BINARY_NAME" "$TARGET_FILE"
fi

echo ""
echo "✅ shai installed successfully to $TARGET_FILE"
echo ""
echo "--- IMPORTANT: Next Steps ---"
echo ""
echo "shai requires a Google AI API key to function."
echo "1. Get your key from Google AI Studio."
echo "2. Add the key to your shell's startup file (e.g., in your .env or ~/.zshrc)."
echo ""
echo "   # Add these two lines to ~/.zshrc:"
echo "   export GOOGLE_GENERATIVE_AI_API_KEY=\"YOUR_API_KEY_GOES_HERE\""
echo "   eval \"\$(shai --zsh-init)\""
echo ""
echo "3. Restart your shell or run: source ~/.zshrc"
