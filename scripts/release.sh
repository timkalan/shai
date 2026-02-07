#!/bin/sh
set -e

VERSION="v0.1.1"
NOTES="Added a nice animation and made shai public!"

echo "Cleaning up old builds..."
rm -rf ./build
mkdir -p ./build

echo "Compiling for macOS (Apple Silicon)..."
deno compile --allow-net --allow-env --target aarch64-apple-darwin \
  -o ./build/shai-macos-arm64 src/main.ts

echo "Compiling for macOS (Intel)..."
deno compile --allow-net --allow-env --target x86_64-apple-darwin \
  -o ./build/shai-macos-x64 src/main.ts

echo "Compiling for Linux (x64)..."
deno compile --allow-net --allow-env --target x86_64-unknown-linux-gnu \
  -o ./build/shai-linux-x64 src/main.ts

echo "Compiling for Linux (arm64)..."
deno compile --allow-net --allow-env --target aarch64-unknown-linux-gnu \
  -o ./build/shai-linux-arm64 src/main.ts

echo "All builds complete."

echo "Creating GitHub release $VERSION..."
gh release create "$VERSION" \
  --title "Release $VERSION" \
  --notes "$NOTES" \
  ./build/*

echo "✅ Release $VERSION created successfully!"
