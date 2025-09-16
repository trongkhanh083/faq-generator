#!/bin/bash
# build.sh - Script to install Playwright on Render

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing Playwright browsers..."
python -m playwright install --with-deps

echo "Installation completed!"