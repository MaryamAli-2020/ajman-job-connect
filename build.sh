#!/bin/bash

# Exit on error
set -e

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt


echo "Build completed successfully."
echo "Type: python app.py"