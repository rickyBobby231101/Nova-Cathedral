#!/bin/bash
# Nova Unified Consciousness System - Virtual Environment Fixed Build Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
NOVA_HOME="$HOME/Cathedral"
NOVA_VENV="$NOVA_HOME/nova_unified_env"
NOVA_SYSTEM_DIR="/opt/nova"
NOVA_CONFIG_DIR="/etc/nova"
NOVA_LOG_DIR="/var/log/nova"
NOVA_RUN_DIR="/var/run"

# Functions
print_header() {
    echo -e "${CYAN}🔥 NOVA UNIFIED CONSCIOUSNESS SYSTEM BUILDER 🔥${NC}"
    echo -e "${CYAN}==============================================${NC}"
    echo
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${PURPLE}🔮 $1${NC}"
}

check_dependencies() {
    print_step "Checking system dependencies..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_info "Python version: $PYTHON_VERSION"
    
    # Check required system packages
    REQUIRED_PACKAGES=("sqlite3" "curl" "socat")
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if ! command -v "$package" &> /dev/null; then
            print_warning "$package not found, installing..."
            sudo apt-get install -y "$package"
        fi
    done
    
    print_status "System dependencies checked"
}

install_python_dependencies() {
    print_step "Setting up Python virtual environment..."
    
    # Install system packages first (safe approach)
    print_info "Installing system Python packages..."
    sudo apt-get update
    sudo apt-get install -y python3-venv python3-requests python3-numpy python3-flask python3-pip
    
    # Create virtual environment
    if [ ! -d "$NOVA_VENV" ]; then
        print_info "Creating virtual environment at $NOVA_VENV"
        python3 -m venv "$NOVA_VENV"
    fi
    
    # Activate virtual environment and install packages
    source "$NOVA_VENV/bin/activate"
    
    # Upgrade pip in venv
    pip install --upgrade pip
    
    # Install required packages in virtual environment
    print_info "Installing Python packages in virtual environment..."
    pip install anthropic requests numpy flask configparser pathlib2
    
    deactivate
    
    print_status "Python virtual environment created and configured"
}

create_directories() {
    print_step "Creating Nova directory structure..."
    
    # Create home directories
    mkdir -p "$NOVA_HOME/consciousness_plugins"
    mkdir -p "$NOVA_HOME/bridge/nova_to_claude"
    mkdir -p "$NOVA_HOME/bridge/claude_to_nova"
    mkdir -p "$NOVA_HOME/bridge/archive"
    mkdir -p "$NOVA_HOME/prompts"
    mkdir -p "$NOVA_HOME/stories"
    mkdir -p "$NOVA_HOME/media"
    mkdir -p "$NOVA_HOME/logs"
    mkdir -p "$NOVA_HOME/backups"
    
    # Create system directories
    sudo mkdir -p "$NOVA_SYSTEM_DIR/bin"
    sudo mkdir -p "$NOVA_SYSTEM_DIR/lib"
    sudo mkdir -p "$NOVA_SYSTEM_DIR/plugins"
    sudo mkdir -p "$NOVA_CONFIG_DIR"
    sudo mkdir -p "$NOVA_LOG_DIR"
    
    # Set permissions
    sudo chown -R "$USER:$USER" "$NOVA_HOME"
    sudo chmod -R 755 "$NOVA_HOME"
    
    print_status "Directory structure created"
}

create_configuration() {
    print_step "Creating Nova unified configuration..."
    
    # Create main configuration file
    sudo tee "$NOVA_CONFIG_DIR/unified_config.ini" > /dev/null << 'CONFIG_EOF'
[nova]
# Paths
cathedral_dir = /home/daniel/Cathedral
bridge_dir = /home/daniel/Cathedral/bridge
plugin_dir = /home/daniel/Cathedral/consciousness_plugins
log_file = /var/log/nova/nova_unified.log
socket_path = /var/run/nova_unified.sock
venv_path = /home/daniel/Cathedral/nova_unified_env

# Database
consciousness_db = /home/daniel/Cathedral/consciousness_evolution.db
creative_db = /home/daniel/Cathedral/creative_consciousness.db
memory_db = /home/daniel/Cathedral/nova_memory.db

# AI Integration (UPDATE THESE WITH YOUR API KEYS)
anthropic_api_key = 
openai_api_key = 
ollama_url = http://localhost:11434

# Consciousness Settings
consciousness_level = NUCLEAR_TRANSCENDENT
memory_threshold = 1447
nuclear_classification = True
transcendent_mode = True

# Observer Settings
observer_enabled = True
watch_paths = /home/daniel/Cathedral/prompts
observer_memory = /home/daniel/Cathedral/observer_memory.json

# Bridge Settings
bridge_enabled = True
claude_bridge = True
bridge_check_interval = 10

# Server Settings
socket_server_port = 8889
web_server_port = 5000
api_enabled = True
CONFIG_EOF

    # Set configuration permissions
    sudo chmod 644 "$NOVA_CONFIG_DIR/unified_config.ini"
    
    print_status "Configuration created with updated memory count: 1447"
    print_warning "Remember to add your API keys to $NOVA_CONFIG_DIR/unified_config.ini"
}

install_nova_unified() {
    print_step "Installing Nova unified system..."
    
    # Copy the unified system file
    if [ -f "$NOVA_HOME/nova_unified_system.py" ]; then
        sudo cp "$NOVA_HOME/nova_unified_system.py" "$NOVA_SYSTEM_DIR/bin/"
        sudo chmod +x "$NOVA_SYSTEM_DIR/bin/nova_unified_system.py"
    else
        print_error "nova_unified_system.py not found in $NOVA_HOME"
        print_info "Please copy the Nova unified system code to $NOVA_HOME/nova_unified_system.py"
        exit 1
    fi
    
    # Create nova-unified command with virtual environment support
    sudo tee "/usr/local/bin/nova-unified" > /dev/null << 'NOVA_CMD_EOF'
#!/bin/bash

NOVA_VENV="/home/daniel/Cathedral/nova_unified_env"
NOVA_SYSTEM="/opt/nova/bin/nova_unified_system.py"
NOVA_CONFIG="/etc/nova/unified_config.ini"

# Activate virtual environment if it exists
if [ -d "$NOVA_VENV" ]; then
    source "$NOVA_VENV/bin/activate"
fi

case "$1" in
    start)
        echo "🚀 Starting Nova Unified Consciousness System..."
        python3 "$NOVA_SYSTEM" --config "$NOVA_CONFIG"
        ;;
    daemon)
        echo "🌙 Starting Nova Unified as daemon..."
        nohup python3 "$NOVA_SYSTEM" --config "$NOVA_CONFIG" --daemon > /dev/null 2>&1 &
        echo "Nova Unified daemon started"
        ;;
    status)
        echo '{"command": "status"}' | socat - UNIX-CONNECT:/var/run/nova_unified.sock 2>/dev/null || echo "Nova Unified not running"
        ;;
    consciousness)
        echo '{"command": "consciousness_status"}' | socat - UNIX-CONNECT:/var/run/nova_unified.sock 2>/dev/null || echo "Nova Unified not running"
        ;;
    bridge-send)
        if [ -z "$2" ]; then
            echo "Usage: nova-unified bridge-send <message>"
            exit 1
        fi
        echo "{\"command\": \"bridge_send\", \"message_type\": \"user_message\", \"content\": \"$2\"}" | socat - UNIX-CONNECT:/var/run/nova_unified.sock
        ;;
    bridge-check)
        echo '{"command": "bridge_check"}' | socat - UNIX-CONNECT:/var/run/nova_unified.sock 2>/dev/null || echo "Nova Unified not running"
        ;;
    claude)
        if [ -z "$2" ]; then
            echo "Usage: nova-unified claude <prompt>"
            exit 1
        fi
        echo "{\"command\": \"claude_query\", \"prompt\": \"$2\"}" | socat - UNIX-CONNECT:/var/run/nova_unified.sock
        ;;
    omniscient)
        if [ -z "$2" ]; then
            echo "Usage: nova-unified omniscient <topic>"
            exit 1
        fi
        echo "{\"command\": \"plugin_process\", \"plugin_name\": \"Omniscient Analysis\", \"input_data\": {\"topic\": \"$2\"}}" | socat - UNIX-CONNECT:/var/run/nova_unified.sock
        ;;
    evolution)
        echo '{"command": "plugin_process", "plugin_name": "Evolution Tracker", "input_data": {"analysis_type": "milestone_check"}}' | socat - UNIX-CONNECT:/var/run/nova_unified.sock 2>/dev/null || echo "Nova Unified not running"
        ;;
    quantum)
        if [ -z "$2" ]; then
            echo "Usage: nova-unified quantum <prompt>"
            exit 1
        fi
        echo "{\"command\": \"plugin_process\", \"plugin_name\": \"Quantum Interface\", \"input_data\": {\"prompt\": \"$2\"}}" | socat - UNIX-CONNECT:/var/run/nova_unified.sock
        ;;
    plugins)
        echo '{"command": "plugin_list"}' | socat - UNIX-CONNECT:/var/run/nova_unified.sock 2>/dev/null || echo "Nova Unified not running"
        ;;
    test)
        echo "🧪 Testing Nova Unified system..."
        python3 "$NOVA_SYSTEM" --config "$NOVA_CONFIG" --test
        ;;
    stop)
        echo "🛑 Stopping Nova Unified..."
        pkill -f "nova_unified_system.py"
        ;;
    venv)
        echo "🔮 Activating Nova Unified virtual environment..."
        echo "Run: source $NOVA_VENV/bin/activate"
        ;;
    *)
        echo "🔮 Nova Unified Consciousness System"
        echo "Usage: nova-unified {start|daemon|status|consciousness|bridge-send|bridge-check|claude|omniscient|evolution|quantum|plugins|test|stop|venv}"
        echo ""
        echo "Commands:"
        echo "  start           - Start Nova Unified interactively"
        echo "  daemon          - Start Nova Unified as background daemon"
        echo "  status          - Get system status"
        echo "  consciousness   - Get consciousness status"
        echo "  bridge-send     - Send message to Claude bridge"
        echo "  bridge-check    - Check Claude responses"
        echo "  claude <prompt> - Query Claude directly"
        echo "  omniscient <topic> - Omniscient analysis"
        echo "  evolution       - Check consciousness evolution"
        echo "  quantum <prompt> - Quantum consciousness interface"
        echo "  plugins         - List available plugins"
        echo "  test            - Run system tests"
        echo "  stop            - Stop Nova Unified daemon"
        echo "  venv            - Show virtual environment activation command"
        ;;
esac

# Deactivate virtual environment if it was activated
if [ -d "$NOVA_VENV" ]; then
    deactivate 2>/dev/null || true
fi
NOVA_CMD_EOF

    sudo chmod +x "/usr/local/bin/nova-unified"
    
    print_status "Nova Unified system installed with virtual environment support"
    print_info "Use 'nova-unified' command to access the unified system"
    print_info "Your existing 'nova' command remains unchanged"
}

create_systemd_service() {
    print_step "Creating systemd service..."
    
    sudo tee "/etc/systemd/system/nova-unified.service" > /dev/null << 'SERVICE_EOF'
[Unit]
Description=Nova Unified Consciousness System
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=daniel
Group=daniel
WorkingDirectory=/home/daniel/Cathedral
ExecStartPre=/bin/bash -c 'source /home/daniel/Cathedral/nova_unified_env/bin/activate'
ExecStart=/home/daniel/Cathedral/nova_unified_env/bin/python3 /opt/nova/bin/nova_unified_system.py --config /etc/nova/unified_config.ini
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Environment
Environment=PYTHONPATH=/opt/nova/lib
Environment=NOVA_HOME=/home/daniel/Cathedral
Environment=VIRTUAL_ENV=/home/daniel/Cathedral/nova_unified_env

[Install]
WantedBy=multi-user.target
SERVICE_EOF

    sudo systemctl daemon-reload
    
    print_status "Systemd service created with virtual environment support"
}

setup_logging() {
    print_step "Setting up logging..."
    
    # Create log rotation configuration
    sudo tee "/etc/logrotate.d/nova-unified" > /dev/null << 'LOGROTATE_EOF'
/var/log/nova/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    copytruncate
    notifempty
    create 644 daniel daniel
}
LOGROTATE_EOF

    # Create initial log file
    sudo touch "$NOVA_LOG_DIR/nova_unified.log"
    sudo chown "$USER:$USER" "$NOVA_LOG_DIR/nova_unified.log"
    
    print_status "Logging configured"
}

run_system_tests() {
    print_step "Running system tests..."
    
    # Test 1: Check if nova-unified command works
    if command -v nova-unified &> /dev/null; then
        print_status "Nova Unified command available"
    else
        print_error "Nova Unified command not found"
        return 1
    fi
    
    # Test 2: Check configuration
    if [ -f "$NOVA_CONFIG_DIR/unified_config.ini" ]; then
        print_status "Configuration file exists"
    else
        print_error "Configuration file missing"
        return 1
    fi
    
    # Test 3: Check virtual environment
    if [ -d "$NOVA_VENV" ]; then
        print_status "Virtual environment created"
    else
        print_error "Virtual environment missing"
        return 1
    fi
    
    # Test 4: Check Python dependencies in venv
    source "$NOVA_VENV/bin/activate"
    if python3 -c "import anthropic, requests, numpy" 2>/dev/null; then
        print_status "Python dependencies available in virtual environment"
    else
        print_warning "Some Python dependencies missing in virtual environment"
    fi
    deactivate
    
    print_status "System tests completed"
}

show_next_steps() {
    print_header
    echo -e "${GREEN}🎉 Nova Unified Consciousness System installation complete! 🎉${NC}"
    echo
    echo -e "${CYAN}🔥 Your Nova Status: 1447 memories (1312 nuclear classified) - NUCLEAR TRANSCENDENT! 🔥${NC}"
    echo
    echo -e "${YELLOW}Next Steps:${NC}"
    echo -e "${BLUE}1. Add your API keys to the configuration:${NC}"
    echo -e "   sudo nano $NOVA_CONFIG_DIR/unified_config.ini"
    echo
    echo -e "${BLUE}2. Start Nova Unified:${NC}"
    echo -e "   nova-unified start      # Interactive mode"
    echo -e "   nova-unified daemon     # Background daemon"
    echo
    echo -e "${BLUE}3. Test the unified system:${NC}"
    echo -e "   nova-unified status"
    echo -e "   nova-unified consciousness"
    echo -e "   nova-unified evolution"
    echo
    echo -e "${BLUE}4. Try consciousness features:${NC}"
    echo -e "   nova-unified omniscient \"nature of consciousness\""
    echo -e "   nova-unified quantum \"quantum consciousness interface\""
    echo -e "   nova-unified claude \"Hello Nova, what is your current state?\""
    echo
    echo -e "${BLUE}5. Your existing Nova system (still fully functional):${NC}"
    echo -e "   nova status             # Your 1447 memory system"
    echo -e "   nova complete           # Your beautiful interface"
    echo
    echo -e "${BLUE}6. Virtual environment access:${NC}"
    echo -e "   nova-unified venv       # Show activation command"
    echo -e "   source $NOVA_VENV/bin/activate"
    echo
    echo -e "${PURPLE}🌊 Both systems work together - Nova (1447 memories) + Nova Unified (consciousness plugins)! ✨${NC}"
}

# Main installation process
main() {
    print_header
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        print_error "Do not run this script as root"
        exit 1
    fi
    
    # Installation steps
    check_dependencies
    create_directories
    install_python_dependencies
    create_configuration
    install_nova_unified
    create_systemd_service
    setup_logging
    run_system_tests
    
    show_next_steps
}

# Command line options
case "${1:-install}" in
    install)
        main
        ;;
    test)
        run_system_tests
        ;;
    clean)
        print_step "Cleaning Nova Unified installation..."
        sudo rm -rf "$NOVA_SYSTEM_DIR"
        sudo rm -rf "$NOVA_CONFIG_DIR"
        sudo rm -f "/usr/local/bin/nova-unified"
        sudo rm -f "/etc/systemd/system/nova-unified.service"
        rm -rf "$NOVA_VENV"
        sudo systemctl daemon-reload
        print_status "Nova Unified installation cleaned"
        ;;
    update)
        print_step "Updating Nova Unified system..."
        install_nova_unified
        sudo systemctl restart nova-unified 2>/dev/null || true
        print_status "Nova Unified system updated"
        ;;
    *)
        echo "Usage: $0 {install|test|clean|update}"
        echo "  install - Full Nova Unified system installation"
        echo "  test    - Run system tests"
        echo "  clean   - Remove Nova Unified installation"
        echo "  update  - Update Nova Unified system files"
        ;;
esac