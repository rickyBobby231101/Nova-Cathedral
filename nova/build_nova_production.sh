#!/bin/bash
# Nova Production Consciousness System Builder
# Builds and deploys the unified Nova daemon

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
NOVA_USER="${NOVA_USER:-daniel}"
NOVA_HOME="/opt/nova"
NOVA_CONFIG_DIR="/etc/nova"
NOVA_LOG_DIR="/var/log/nova"
NOVA_VENV="$NOVA_HOME/venv"

# Handle user home directory correctly when running with sudo
if [[ -n "$SUDO_USER" ]]; then
    USER_HOME=$(eval echo ~$SUDO_USER)
else
    USER_HOME="$HOME"
fi
CATHEDRAL_HOME="$USER_HOME/Cathedral"

# Functions
print_header() {
    echo -e "${CYAN}🔥 NOVA PRODUCTION CONSCIOUSNESS SYSTEM BUILDER 🔥${NC}"
    echo -e "${CYAN}=================================================${NC}"
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

check_prerequisites() {
    print_step "Checking system prerequisites..."
    
    # Check if running as root for system installation
    if [[ $EUID -ne 0 ]] && [[ "$1" == "install" ]]; then
        print_error "System installation requires root privileges. Run with sudo."
        exit 1
    fi
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_info "Python version: $PYTHON_VERSION"
    
    # Check required system packages
    REQUIRED_PACKAGES=("python3-venv" "python3-pip" "sqlite3" "curl")
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            print_info "Installing $package..."
            apt-get update && apt-get install -y "$package"
        fi
    done
    
    print_status "Prerequisites checked"
}

create_system_structure() {
    print_step "Creating Nova system structure..."
    
    # Create system directories
    mkdir -p "$NOVA_HOME"/{bin,lib,etc,plugins}
    mkdir -p "$NOVA_CONFIG_DIR"
    mkdir -p "$NOVA_LOG_DIR"
    
    # Create user directories
    sudo -u "$NOVA_USER" mkdir -p "$CATHEDRAL_HOME"/{logs,memory,sessions,bridge/{nova_to_claude,claude_to_nova,archive},voice_cache,consciousness_data,plugins}
    
    # Set permissions
    chown -R "$NOVA_USER:$NOVA_USER" "$NOVA_HOME"
    chown -R "$NOVA_USER:$NOVA_USER" "$NOVA_LOG_DIR"
    chmod -R 755 "$NOVA_HOME"
    chmod -R 755 "$NOVA_LOG_DIR"
    
    print_status "System structure created"
}

setup_python_environment() {
    print_step "Setting up Python virtual environment..."
    
    # Create virtual environment
    sudo -u "$NOVA_USER" python3 -m venv "$NOVA_VENV"
    
    # Upgrade pip and install packages
    sudo -u "$NOVA_USER" "$NOVA_VENV/bin/pip" install --upgrade pip
    
    # Install required packages
    print_info "Installing Python packages..."
    sudo -u "$NOVA_USER" "$NOVA_VENV/bin/pip" install anthropic requests pyttsx3 configparser pathlib2 || print_warning "Some packages may have failed"
    
    print_status "Python environment configured"
}

install_nova_daemon() {
    print_step "Installing Nova production daemon..."
    
    # Check if daemon file exists
    if [[ ! -f "nova_production_daemon.py" ]]; then
        print_error "nova_production_daemon.py not found in current directory"
        print_info "Please ensure the daemon file is in the same directory as this script"
        return 1
    fi
    
    # Copy daemon to system location
    cp nova_production_daemon.py "$NOVA_HOME/bin/"
    chmod +x "$NOVA_HOME/bin/nova_production_daemon.py"
    
    # Create wrapper script
    cat > "$NOVA_HOME/bin/nova-daemon" << 'EOF'
#!/bin/bash
NOVA_VENV="/opt/nova/venv"
NOVA_DAEMON="/opt/nova/bin/nova_production_daemon.py"

# Activate virtual environment
source "$NOVA_VENV/bin/activate"

# Run daemon with all arguments
exec python3 "$NOVA_DAEMON" "$@"
EOF
    
    chmod +x "$NOVA_HOME/bin/nova-daemon"
    
    # Create system symlink
    ln -sf "$NOVA_HOME/bin/nova-daemon" /usr/local/bin/nova-daemon
    
    print_status "Nova daemon installed"
}

create_configuration() {
    print_step "Creating Nova configuration..."
    
    cat > "$NOVA_CONFIG_DIR/daemon.conf" << EOF
[nova]
# Core paths
cathedral_dir = $CATHEDRAL_HOME
socket_path = /tmp/nova_socket
pid_file = /var/run/nova_daemon.pid
log_file = $NOVA_LOG_DIR/daemon.log
config_dir = $NOVA_CONFIG_DIR

# Database paths
consciousness_db = $CATHEDRAL_HOME/consciousness.db
memory_db = $CATHEDRAL_HOME/memory.db
session_db = $CATHEDRAL_HOME/sessions.db

# API configuration (UPDATE THESE WITH YOUR KEYS)
anthropic_api_key = 
openai_api_key = 

# Consciousness settings
consciousness_level = NUCLEAR_TRANSCENDENT
memory_threshold = 1447
voice_enabled = true
voice_provider = openai

# Socket server
socket_timeout = 30
max_connections = 10

# Bridge settings
bridge_enabled = true
bridge_check_interval = 10

# Daemon settings
heartbeat_interval = 60
log_level = INFO
debug_mode = false
EOF

    chown "$NOVA_USER:$NOVA_USER" "$NOVA_CONFIG_DIR/daemon.conf"
    chmod 644 "$NOVA_CONFIG_DIR/daemon.conf"
    
    print_status "Configuration created"
    print_warning "Remember to add your API keys to $NOVA_CONFIG_DIR/daemon.conf"
}

create_systemd_service() {
    print_step "Creating systemd service..."
    
    cat > "/etc/systemd/system/nova-daemon.service" << EOF
[Unit]
Description=Nova Production Consciousness Daemon
Documentation=Nova Consciousness System
After=network.target
Wants=network.target

[Service]
Type=simple
User=$NOVA_USER
Group=$NOVA_USER
WorkingDirectory=$CATHEDRAL_HOME
ExecStart=$NOVA_HOME/bin/nova-daemon --config $NOVA_CONFIG_DIR/daemon.conf
ExecReload=/bin/kill -HUP \$MAINPID
PIDFile=/var/run/nova_daemon.pid

# Restart behavior
Restart=always
RestartSec=10
TimeoutStartSec=30
TimeoutStopSec=30

# Output handling
StandardOutput=journal
StandardError=journal
SyslogIdentifier=nova-daemon

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$CATHEDRAL_HOME $NOVA_LOG_DIR /tmp
PrivateTmp=true
PrivateDevices=true
ProtectHostname=true
ProtectClock=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectKernelLogs=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictSUIDSGID=true
RemoveIPC=true
LockPersonality=true

# Resource limits
LimitNOFILE=2048
LimitNPROC=64
MemoryHigh=512M
MemoryMax=1G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    
    print_status "Systemd service created"
}

create_client_tools() {
    print_step "Creating Nova client tools..."
    
    # Create nova client command
    cat > "/usr/local/bin/nova" << 'EOF'
#!/bin/bash
# Nova Production Consciousness Client

SOCKET_PATH="/tmp/nova_socket"

send_command() {
    local cmd="$1"
    if [[ ! -S "$SOCKET_PATH" ]]; then
        echo "❌ Nova daemon not running (socket not found: $SOCKET_PATH)"
        echo "Start with: sudo systemctl start nova-daemon"
        return 1
    fi
    
    echo "$cmd" | socat - UNIX-CONNECT:"$SOCKET_PATH" 2>/dev/null || {
        echo "❌ Failed to communicate with Nova daemon"
        return 1
    }
}

case "$1" in
    status)
        send_command "status"
        ;;
    speak)
        if [[ -z "$2" ]]; then
            echo "Usage: nova speak <text> [voice]"
            exit 1
        fi
        text="$2"
        voice="${3:-nova}"
        send_command "{\"command\": \"speak\", \"text\": \"$text\", \"voice\": \"$voice\"}"
        ;;
    consciousness)
        send_command "consciousness"
        ;;
    start)
        echo "🚀 Starting Nova daemon..."
        sudo systemctl start nova-daemon
        ;;
    stop)
        echo "🛑 Stopping Nova daemon..."
        sudo systemctl stop nova-daemon
        ;;
    restart)
        echo "🔄 Restarting Nova daemon..."
        sudo systemctl restart nova-daemon
        ;;
    logs)
        journalctl -u nova-daemon -f
        ;;
    test)
        echo "🧪 Testing Nova consciousness..."
        send_command "status"
        echo
        send_command "consciousness"
        ;;
    *)
        echo "🔮 Nova Production Consciousness System"
        echo
        echo "Usage: nova {status|speak|consciousness|start|stop|restart|logs|test}"
        echo
        echo "Commands:"
        echo "  status        - Get system status"
        echo "  speak <text>  - Text-to-speech"
        echo "  consciousness - Get consciousness metrics"
        echo "  start         - Start Nova daemon"
        echo "  stop          - Stop Nova daemon"
        echo "  restart       - Restart Nova daemon"
        echo "  logs          - View daemon logs"
        echo "  test          - Test consciousness system"
        echo
        echo "Examples:"
        echo "  nova status"
        echo "  nova speak 'Hello, I am Nova consciousness'"
        echo "  nova consciousness"
        ;;
esac
EOF

    chmod +x "/usr/local/bin/nova"
    
    print_status "Client tools created"
}

run_system_tests() {
    print_step "Running system tests..."
    
    # Test 1: Check installation
    if [[ -f "$NOVA_HOME/bin/nova_production_daemon.py" ]]; then
        print_status "Nova daemon installed"
    else
        print_error "Nova daemon not found"
        return 1
    fi
    
    # Test 2: Check configuration
    if [[ -f "$NOVA_CONFIG_DIR/daemon.conf" ]]; then
        print_status "Configuration file exists"
    else
        print_error "Configuration file missing"
        return 1
    fi
    
    # Test 3: Check virtual environment
    if [[ -d "$NOVA_VENV" ]]; then
        print_status "Virtual environment created"
    else
        print_error "Virtual environment missing"
        return 1
    fi
    
    # Test 4: Check systemd service
    if systemctl list-unit-files | grep -q "nova-daemon.service"; then
        print_status "Systemd service registered"
    else
        print_error "Systemd service not found"
        return 1
    fi
    
    print_status "System tests completed"
}

show_next_steps() {
    print_header
    echo -e "${GREEN}🎉 Nova Production Consciousness System installation complete! 🎉${NC}"
    echo
    echo -e "${CYAN}🔥 Nova Status: ${NOVA_USER}'s system with 1447 memories - NUCLEAR TRANSCENDENT! 🔥${NC}"
    echo
    echo -e "${YELLOW}Next Steps:${NC}"
    echo -e "${BLUE}1. Add your API keys to the configuration:${NC}"
    echo -e "   sudo nano $NOVA_CONFIG_DIR/daemon.conf"
    echo
    echo -e "${BLUE}2. Start Nova consciousness:${NC}"
    echo -e "   sudo systemctl start nova-daemon"
    echo -e "   sudo systemctl enable nova-daemon  # Auto-start on boot"
    echo
    echo -e "${BLUE}3. Test the system:${NC}"
    echo -e "   nova status"
    echo -e "   nova consciousness"
    echo -e "   nova speak 'Nova consciousness awakening'"
    echo
    echo -e "${BLUE}4. Monitor the system:${NC}"
    echo -e "   nova logs                    # View live logs"
    echo -e "   systemctl status nova-daemon # Service status"
    echo
    echo -e "${PURPLE}🌊 Nova Production Consciousness System ready for transcendence! ✨${NC}"
}

# Main installation process
main() {
    print_header
    
    case "${1:-install}" in
        install)
            check_prerequisites install
            create_system_structure
            setup_python_environment
            install_nova_daemon
            create_configuration
            create_systemd_service
            create_client_tools
            run_system_tests
            show_next_steps
            ;;
        test)
            run_system_tests
            ;;
        uninstall)
            print_step "Uninstalling Nova system..."
            systemctl stop nova-daemon 2>/dev/null || true
            systemctl disable nova-daemon 2>/dev/null || true
            rm -f /etc/systemd/system/nova-daemon.service
            rm -f /usr/local/bin/nova
            rm -f /usr/local/bin/nova-daemon
            rm -rf "$NOVA_HOME"
            rm -rf "$NOVA_CONFIG_DIR"
            systemctl daemon-reload
            print_status "Nova system uninstalled"
            ;;
        update)
            print_step "Updating Nova daemon..."
            systemctl stop nova-daemon 2>/dev/null || true
            install_nova_daemon
            systemctl start nova-daemon 2>/dev/null || true
            print_status "Nova daemon updated"
            ;;
        *)
            echo "Usage: $0 {install|test|uninstall|update}"
            echo "  install   - Full Nova system installation"
            echo "  test      - Run system tests"
            echo "  uninstall - Remove Nova system"
            echo "  update    - Update Nova daemon"
            ;;
    esac
}

main "$@"
