#!/bin/bash
# Library repository update script
# Usage: ./update_library.sh

LIBRARY_DIR="./input/library"

echo "=== Utayomi Library Update Script ==="

# Check if library directory exists and is a git repository
if [ ! -d "$LIBRARY_DIR" ]; then
    echo "Error: Library directory not found: $LIBRARY_DIR"
    exit 1
fi

cd "$LIBRARY_DIR"

if [ ! -d ".git" ]; then
    echo "Error: Not a git repository: $LIBRARY_DIR"
    exit 1
fi

echo "Current directory: $(pwd)"
echo "Remote repository: $(git remote get-url origin)"

# Check for local changes
if [ -n "$(git status --porcelain)" ]; then
    echo "Warning: Local changes detected."
    echo "Local changes:"
    git status --short
    
    read -p "Do you want to discard local changes and update? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Discarding local changes..."
        git restore .
        git clean -fd
    else
        echo "Update cancelled. Please handle local changes manually."
        exit 1
    fi
fi

# Fetch and pull latest changes
echo "Fetching latest changes..."
git fetch origin

echo "Updating to latest version..."
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ Library updated successfully!"
    echo "Latest commit:"
    git log -1 --oneline
else
    echo "❌ Update failed. Please check the error messages above."
    exit 1
fi

echo "=== Update completed ==="