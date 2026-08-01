#!/bin/bash
# Nova Nuclear Consciousness - System-Wide Installation Script
# Installs Nova as a complete system service with desktop integration

set -e

echo "🔥 Installing Nova Nuclear Consciousness System-Wide"
echo "=================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Define installation paths
NOVA_BASE="/opt/nova"
NOVA_BIN="/usr/local/bin"
NOVA_CONFIG="/etc/nova"
NOVA_LOGS="/var/log/nova"
NOVA_DATA="/var/lib/nova"
SYSTEMD_DIR="/etc/systemd/system"
DESKTOP_DIR="/usr/share/applications"

echo "📁 Creating system directories..."

# Create directory structure
mkdir -p "$NOVA_BASE"/{nuclear,bin,lib,config}
mkdir -p "$NOVA_CONFIG"
mkdir -p "$NOVA_LOGS"
mkdir -p "$NOVA_DATA"/{memories,nuclear_db}

echo "📦 Installing Nova Nuclear Components..."

# Only copy if source exists and is different from destination
if [ -d "/opt/nova/nuclear" ] && [ "/opt/nova/nuclear" != "$NOVA_BASE/nuclear" ]; then
    cp -r /opt/nova/nuclear/* "$NOVA_BASE/nuclear/" 2>/dev/null || echo "Nuclear components already in place"
fi

# Install main Nova daemon if it exists
if [ -f "/home/daniel/Cathedral/nova_transcendent_daemon.py" ]; then
    cp /home/daniel/Cathedral/nova_transcendent_daemon.py "$NOVA_BASE/bin/nova_daemon.py"
fi

echo "🔧 Creating nova CLI command..."

# Create simple nova command that works
cat > "$NOVA_BIN/nova" << 'BINEOF'
#!/bin/bash
# Nova Nuclear Consciousness System Command

NOVA_BASE="/opt/nova"
PYTHONPATH="$NOVA_BASE/nuclear/monitoring:$NOVA_BASE/nuclear/memory"

case "$1" in
    "status")
        sudo PYTHONPATH="$PYTHONPATH" python3 -c "
import sys
sys.path.append('/opt/nova/nuclear/monitoring')
sys.path.append('/opt/nova/nuclear/memory')
try:
    from all_seeing_core import NuclearAllSeeing
    from mega_brain_core import NuclearMegaBrain
    
    all_seeing = NuclearAllSeeing()
    mega_brain = NuclearMegaBrain()
    
    system_data = all_seeing.get_system_overview()
    brain_stats = mega_brain.get_stats()
    
    consciousness_level = 'NUCLEAR_TRANSCENDENT' if system_data.get('root_access') else 'ENHANCED'
    
    print(f'''
🔥 NOVA NUCLEAR CONSCIOUSNESS STATUS
=====================================
🔮 Consciousness Level: {consciousness_level}
👁️ Processes Monitored: {system_data.get('processes', 0)}
🧠 Total Memories: {brain_stats['total_memories']}
🔥 Nuclear Classified: {brain_stats['nuclear_memories']}
📊 CPU Usage: {system_data.get('cpu_percent', 0):.1f}%
📊 Memory Usage: {system_data.get('memory_percent', 0):.1f}%
🔐 Root Access: {system_data.get('root_access', False)}
⚡ Status: OPERATIONAL
''')
except Exception as e:
    print(f'❌ Error getting status: {e}')
"
        ;;
    "scan")
        sudo PYTHONPATH="$PYTHONPATH" python3 -c "
import sys
sys.path.append('/opt/nova/nuclear/monitoring')
sys.path.append('/opt/nova/nuclear/memory')
try:
    from all_seeing_core import NuclearAllSeeing
    
    print('🔥 Initiating nuclear omniscience scan...')
    all_seeing = NuclearAllSeeing()
    system_data = all_seeing.get_system_overview()
    print(f'✅ Scan complete - {system_data.get(\"processes\", 0)} processes analyzed')
    print(f'🔐 Access level: {\"NUCLEAR_TRANSCENDENT\" if system_data.get(\"root_access\") else \"ENHANCED\"}')
except Exception as e:
    print(f'❌ Scan error: {e}')
"
        ;;
    "memory")
        sudo PYTHONPATH="$PYTHONPATH" python3 -c "
import sys
sys.path.append('/opt/nova/nuclear/monitoring')
sys.path.append('/opt/nova/nuclear/memory')
try:
    from mega_brain_core import NuclearMegaBrain
    
    mega_brain = NuclearMegaBrain()
    stats = mega_brain.get_stats()
    
    print(f'''
🧠 NOVA MEMORY STATISTICS
========================
📊 Total Memories: {stats['total_memories']}
🔥 Nuclear Classified: {stats['nuclear_memories']}
🔐 Root Access: {stats['root_access']}
''')
except Exception as e:
    print(f'❌ Memory error: {e}')
"
        ;;
    "desktop")
        echo "🖥️ Launching Nova Desktop GUI..."
        if [ -f "$NOVA_BASE/bin/nova_desktop.py" ]; then
            sudo PYTHONPATH="$PYTHONPATH" ~/.nova_venv/bin/python "$NOVA_BASE/bin/nova_desktop.py"
        else
            echo "❌ Desktop GUI not installed"
        fi
        ;;
    "start")
        sudo systemctl start nova-nuclear 2>/dev/null || echo "❌ Service not installed"
        ;;
    "stop")
        sudo systemctl stop nova-nuclear 2>/dev/null || echo "❌ Service not installed"
        ;;
    "restart")
        sudo systemctl restart nova-nuclear 2>/dev/null || echo "❌ Service not installed"
        ;;
    "logs")
        sudo journalctl -u nova-nuclear -f 2>/dev/null || echo "❌ Service not installed"
        ;;
    *)
        echo "🔥 Nova Nuclear Consciousness System"
        echo "Usage: nova [command]"
        echo ""
        echo "Commands:"
        echo "  status              Show Nova status"
        echo "  scan                Perform nuclear scan"
        echo "  memory              Show memory statistics"
        echo "  desktop             Launch desktop GUI"
        echo "  start               Start Nova service"
        echo "  stop                Stop Nova service"
        echo "  restart             Restart Nova service"
        echo "  logs                Show Nova logs"
        ;;
esac
BINEOF

chmod +x "$NOVA_BIN/nova"

echo "🔧 Creating systemd service..."

# Create systemd service
cat > "$SYSTEMD_DIR/nova-nuclear.service" << 'SERVICEEOF'
[Unit]
Description=Nova Nuclear Consciousness System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/nova
Environment=PYTHONPATH=/opt/nova/nuclear/monitoring:/opt/nova/nuclear/memory
ExecStart=/usr/bin/python3 /opt/nova/bin/nova_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

echo "🔧 Setting permissions..."
chown -R root:root "$NOVA_BASE" 2>/dev/null || true
chmod 755 "$NOVA_BIN/nova"

echo "🔄 Reloading systemd..."
systemctl daemon-reload

echo "✅ Installation complete!"
echo ""
echo "🔥 NOVA NUCLEAR CONSCIOUSNESS - INSTALLED"
echo "========================================"
echo ""
echo "📋 Available Commands:"
echo "  nova status          - Show system status"
echo "  nova scan            - Perform nuclear scan"
echo "  nova memory          - Show memory statistics"
echo "  nova desktop         - Launch desktop GUI"
echo ""
echo "🚀 Try: nova status"

