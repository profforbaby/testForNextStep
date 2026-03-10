#!/bin/bash
# Startup script for Learn & Play Educational App

echo "Starting Learn & Play Educational App..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed!"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if dependencies are installed
if ! python3 -c "import PyQt6" 2>/dev/null; then
    echo ""
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "Loaded environment variables from .env"
fi

# Run the application
echo "Launching application..."
echo ""
python3 app.py
