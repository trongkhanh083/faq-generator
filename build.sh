#!/bin/bash
# build.sh - Manual dependency installation for Render

echo "Installing system dependencies for Playwright..."

# Install minimal dependencies
apt-get update
apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxinerama1 \
    libxss1 \
    libxtst6 \
    libappindicator1 \
    libatspi2.0-0 \
    libuuid1

echo "System dependencies installed."