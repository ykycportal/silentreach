#!/bin/bash
# SilentReach KG Quick Start Script

echo "🧠 SilentReach Knowledge Graph - Setup & Test"
echo "=============================================="
echo ""

# Check if running in Termux
if [ -d "$HOME/.termux" ]; then
    echo "✓ Running on Android/Termux"
else
    echo "⚠ Running on $(uname) - some features may vary"
fi

echo ""
echo "Checking installation..."
python -c "import sys; sys.path.insert(0, '.'); from services.kg_service import KGService; print('✓ KGService imported')" 2>/dev/null || echo "✗ KGService import failed"
python -c "import sys; sys.path.insert(0, '.'); from services.report_generator import MarketingReportGenerator; print('✓ ReportGenerator imported')" 2>/dev/null || echo "✗ ReportGenerator import failed"

echo ""
echo "Running integration test..."
python tests/test_kg_manual.py

echo ""
echo "=============================================="
echo "✅ Integration complete!"
echo ""
echo "Try it:"
echo "  silentreach kg build \"AI marketing\" -p reddit,linkedin"
echo "  silentreach kg query --search \"Shopify\""
echo "  silentreach kg export --format markdown"
echo ""
echo "Output location: ~/.silentreach/reports/"
