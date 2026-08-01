#!/bin/bash
# setup_cathedral.sh — One-shot Nova Cathedral installer
# Run with: bash setup_cathedral.sh

set -e

DEST="$HOME/nova_cathedral"
FEED="$DEST/feed"
DATA="$DEST/data"
LOGS="$DEST/logs"
PLUGINS="$DEST/plugins"

echo "🔮 Setting up Nova Cathedral at $DEST"
echo ""

# Create directory structure
mkdir -p "$DEST" "$FEED" "$DATA" "$LOGS" "$PLUGINS"

echo "✅ Directories created"

# Copy any existing cathedral build files if present
CATHEDRAL_BUILD="$HOME/Desktop/cathedral build 1/cathedral build"
if [ -d "$CATHEDRAL_BUILD" ]; then
    echo "📦 Found existing cathedral build — migrating useful files..."
    for f in echo_module.py oracle_module.py integrated_nova_system.py \
              nova_advanced_plugins.py nova_foundation.yaml crew_manifest.json; do
        if [ -f "$CATHEDRAL_BUILD/$f" ]; then
            cp "$CATHEDRAL_BUILD/$f" "$DEST/$f"
            echo "  ✔ $f"
        fi
    done
    # Copy consciousness DB if it exists
    if [ -f "$CATHEDRAL_BUILD/consciousness.db" ]; then
        cp "$CATHEDRAL_BUILD/consciousness.db" "$DATA/consciousness.db"
        echo "  ✔ consciousness.db (existing memory preserved)"
    fi
fi

echo ""
echo "📜 Nova Cathedral ready at: $DEST"
echo ""
echo "Structure:"
echo "  $DEST/"
echo "  ├── nova_wiring.py          ← entry point"
echo "  ├── nova_memory.py          ← persistent memory"
echo "  ├── echo_module.py"
echo "  ├── oracle_module.py"
echo "  ├── integrated_nova_system.py"
echo "  ├── nova_cathedral_daemon.py"
echo "  ├── plugins/"
echo "  │   ├── nova_evolution.py   ← self-evolution engine"
echo "  │   ├── nova_archivist.py   ← memory search + scroll listing"
echo "  │   └── ask_ai.py"
echo "  ├── feed/                   ← drop files here to teach Nova"
echo "  ├── data/                   ← nova_memory.db lives here"
echo "  └── logs/"
echo ""
echo "To run Nova:"
echo "  cd ~/nova_cathedral && python3 nova_wiring.py"
echo ""
echo "To teach Nova something new:"
echo "  cp any_file.txt ~/nova_cathedral/feed/"
echo "  (Nova will absorb it on next boot)"
