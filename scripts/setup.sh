#!/bin/bash
set -euo pipefail

echo "Setting up DIP development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Initialize git hooks
if [ -d ".git" ]; then
    echo "Setting up pre-commit hooks..."
    pre-commit install
fi

echo ""
echo "Setup complete!"
echo ""
echo "To activate the virtual environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To start the API server:"
echo "  uvicorn services.ingestion.main:app --reload"
echo ""
echo "To run tests:"
echo "  pytest"
echo ""
