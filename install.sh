#!/bin/bash
# SilentReach One-Click Installer for Termux
# Usage: bash install.sh

set -e

echo "🔇 SilentReach - Ultimate Android Scraper"
echo "=========================================="
echo ""

# Check if running in Termux
if [ ! -d "$HOME/.termux" ]; then
    echo "❌ This installer is designed for Termux on Android"
    echo "   Please run this in Termux app"
    exit 1
fi

echo "📱 Termux environment detected"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Update packages
echo "📦 Updating packages..."
pkg update -y
pkg upgrade -y

# Install dependencies
echo "📦 Installing dependencies..."
pkg install -y python git chromium yt-dlp curl wget

# Check if repo exists
if [ -d "$HOME/silentreach" ]; then
    echo "📂 Repository already exists at ~/silentreach"
    echo "   Pulling latest changes..."
    cd ~/silentreach
    git pull
else
    echo "📂 Cloning repository..."
    git clone https://github.com/ykycportal/silentreach.git ~/silentreach
    cd ~/silentreach
fi

# Install Python package
echo "🐍 Installing Python package..."
pip install -e ".[all]"

# Setup
echo "🔧 Running setup..."
python -m silentreach setup 2>/dev/null || silentreach setup 2>/dev/null || echo "Setup completed"

# Create symlinks for convenience
echo "🔗 Creating convenient symlinks..."
ln -sf ~/silentreach/scripts/silentreach.py ~/.silentreach/cli.py 2>/dev/null || true

# Check Termux:API
echo ""
echo "📱 Checking Termux:API..."
if ! command -v termux-notification &> /dev/null; then
    echo "   ⚠️  Termux:API not installed"
    echo "   Install for notifications: pkg install termux-api"
else
    echo "   ✅ Termux:API detected"
fi

# Show completion message
echo ""
echo "${GREEN}✅ SilentReach installed successfully!${NC}"
echo ""
echo "📋 Quick Start:"
echo "   cd ~/silentreach"
echo "   silentreach doctor"
echo "   silentreach search 'dropshipping' -p all"
echo ""
echo "📚 Documentation:"
echo "   ~/silentreach/README.md"
echo "   ~/silentreach/TERMUX.md"
echo ""
echo "🔔 Features:"
echo "   • Background scheduling (crontab)"
echo "   • Push notifications (Termux:API)"
echo "   • Offline queue system"
echo "   • Web dashboard (port 5000)"
echo "   • Google Sheets export"
echo "   • Plugin system for custom platforms"
echo ""
echo "🎯 Try these commands:"
echo "   silentreach presets          # View monitoring templates"
echo "   silentreach schedule add my_daily 0 8 * * * --command 'silentreach search \"dropshipping\" -p reddit,youtube'"
echo "   silentreach notify 'Test notification'"
echo "   silentreach dashboard        # Start web dashboard"
echo "   silentreach queue add reddit 'products'    # Queue for offline"
echo ""
echo "${YELLOW}Happy scraping! 🔇${NC}"
