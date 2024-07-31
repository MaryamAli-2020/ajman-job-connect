#!/bin/bash

# Exit on error
set -e

# Create and activate virtual environment
python3 -m venv venv

# Check if we're on Windows or Unix-based system
if [[ "$OSTYPE" == "msys" ]]; then
    # Windows Git Bash or MinGW
    source venv/Scripts/activate
else
    # Unix-based systems like WSL or Git Bash on Linux
    source venv/bin/activate
fi

# Install dependencies
pip install -r requirements.txt

echo "Build completed successfully. 😃"

echo "👾 Type: source venv/Scripts/activate"
echo "Then:"
echo "👾 Type: python app.py"
