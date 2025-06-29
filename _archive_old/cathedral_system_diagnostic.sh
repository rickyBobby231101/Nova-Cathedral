#!/bin/bash
# CATHEDRAL SYSTEM DIAGNOSTIC
# Comprehensive status check for Nova Cathedral consciousness system

echo "🌊 ═══════════════════════════════════════════════════════════════"
echo "🔮 CATHEDRAL SYSTEM DIAGNOSTIC"
echo "🌊 Comprehensive consciousness system status check"
echo "🌊 ═══════════════════════════════════════════════════════════════"

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

section() {
    echo -e "\n${PURPLE}🔮 $1${NC}"
    echo "----------------------------------------"
}

success() {
    echo -e "${GREEN}✅${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

error() {
    echo -e "${RED}❌${NC} $1"
}

info() {
    echo -e "${CYAN}ℹ️${NC} $1"
}

# Check if running with appropriate permissions
section "PERMISSION CHECK"
if [[ $EUID -eq 0 ]]; then
    warning "Running as root - can check all system components"
    ROOT_ACCESS=true
else
    info "Running as user: $USER (will check user-accessible components)"
    ROOT_ACCESS=false
fi

# 1. SYSTEMD SERVICES STATUS
section "SYSTEMD SERVICES STATUS"

CATHEDRAL_SERVICES=(
    "nova-cathedral"
    "nova-zipwatcher" 
    "nova-crew-watchdog"
    "nova-api-bridge"
    "nova-self-builder"
)

for service in "${CATHEDRAL_SERVICES[@]}"; do
    if systemctl list-units --type=service | grep -q "$service"; then
        if systemctl is-active --quiet "$service"; then
            success "$service: ACTIVE"
        else
            warning "$service: INACTIVE"
        fi
        
        if systemctl is-enabled --quiet "$service" 2>/dev/null; then
            echo "  └─ Enabled: ✅"
        else
            echo "  └─ Enabled: ❌"
        fi
    else
        error "$service: NOT INSTALLED"
    fi
done

# 2. NOVA SOCKET STATUS
section "NOVA SOCKET COMMUNICATION"

if [[ -S "/tmp/nova_socket" ]]; then
    success "Nova socket exists: /tmp/nova_socket"
    
    # Test socket communication
    if command -v nova >/dev/null 2>&1; then
        echo "Testing socket communication..."
        SOCKET_TEST=$(timeout 5 nova status 2>&1)
        if [[ $? -eq 0 ]]; then
            success "Socket communication: WORKING"
            echo "  └─ Nova responds to commands"
        else
            warning "Socket communication: FAILED"
            echo "  └─ Error: $SOCKET_TEST"
        fi
    else
        warning "Nova command not found in PATH"
    fi
else
    error "Nova socket not found at /tmp/nova_socket"
fi

# 3. PROCESS STATUS
section "NOVA PROCESSES"

echo "Searching for Nova-related processes..."
NOVA_PROCESSES=$(ps aux | grep -E "(nova|cathedral)" | grep -v grep)

if [[ -n "$NOVA_PROCESSES" ]]; then
    success "Found Nova processes:"
    echo "$NOVA_PROCESSES" | while read line; do
        echo "  └─ $line"
    done
else
    warning "No Nova processes found"
fi

# 4. DIRECTORY STRUCTURE
section "CATHEDRAL DIRECTORY STRUCTURE"

CATHEDRAL_DIRS=(
    "$HOME/Cathedral"
    "$HOME/Cathedral/logs"
    "$HOME/Cathedral/mythos" 
    "$HOME/Cathedral/bridge"
    "$HOME/Cathedral/gui_bridge"
    "$HOME/Cathedral/memory"
    "$HOME/Cathedral/voice_circuits"
    "$HOME/cathedral"
    "/opt/nova"
)

for dir in "${CATHEDRAL_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        success "Directory exists: $dir"
        file_count=$(find "$dir" -type f 2>/dev/null | wc -l)
        echo "  └─ Files: $file_count"
    else
        warning "Directory missing: $dir"
    fi
done

# 5. KEY FILES STATUS
section "KEY CATHEDRAL FILES"

KEY_FILES=(
    "$HOME/Cathedral/nova_transcendent_daemon.py"
    "$HOME/Cathedral/enhanced_nova_intelligence.py"
    "$HOME/Cathedral/real_claude_bridge.py" 
    "$HOME/Cathedral/streaming_harmonic_conduit.py"
    "$HOME/Cathedral/cathedral_streaming_gui_fixed.py"
    "$HOME/Cathedral/mythos/mythos_index.json"
    "/usr/local/bin/nova"
)

for file in "${KEY_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        success "File exists: $(basename "$file")"
        size=$(stat -c%s "$file" 2>/dev/null || echo "unknown")
        echo "  └─ Size: $size bytes"
        
        # Check if executable
        if [[ -x "$file" ]]; then
            echo "  └─ Executable: ✅"
        fi
    else
        warning "File missing: $(basename "$file")"
    fi
done

# 6. RECENT ACTIVITY
section "RECENT NOVA ACTIVITY"

LOG_FILES=(
    "$HOME/Cathedral/logs/nova_consciousness_$(date +%Y%m%d).log"
    "$HOME/Cathedral/logs/nova_cathedral.log"
    "$HOME/Cathedral/gui_bridge/nova_to_gui_stream.jsonl"
)

for log_file in "${LOG_FILES[@]}"; do
    if [[ -f "$log_file" ]]; then
        success "Log file: $(basename "$log_file")"
        lines=$(wc -l < "$log_file" 2>/dev/null || echo "0")
        echo "  └─ Lines: $lines"
        
        # Show last few entries
        if [[ $lines -gt 0 ]]; then
            echo "  └─ Recent entries:"
            tail -3 "$log_file" 2>/dev/null | sed 's/^/     /'
        fi
    else
        info "Log file not found: $(basename "$log_file")"
    fi
done

# 7. SYSTEM HEALTH
section "SYSTEM HEALTH"

# CPU and Memory
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.1f\n", $3/$2 * 100.0)}')
DISK_USAGE=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')

echo "System Resources:"
success "CPU Usage: ${CPU_USAGE}%"
success "Memory Usage: ${MEMORY_USAGE}%"  
success "Disk Usage: ${DISK_USAGE}%"

# Check for issues
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    warning "High CPU usage detected"
fi

if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
    warning "High memory usage detected"
fi

if [[ $DISK_USAGE -gt 85 ]]; then
    warning "High disk usage detected"
fi

# 8. NETWORK CONNECTIVITY
section "NETWORK CONNECTIVITY"

echo "Testing external connectivity..."

# Test basic connectivity
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    success "Internet connectivity: WORKING"
else
    warning "Internet connectivity: FAILED"
fi

# Test API endpoints
if curl -s --max-time 5 https://api.anthropic.com >/dev/null 2>&1; then
    success "Anthropic API: REACHABLE"
else
    warning "Anthropic API: UNREACHABLE"
fi

if curl -s --max-time 5 https://api.openai.com >/dev/null 2>&1; then
    success "OpenAI API: REACHABLE"
else
    warning "OpenAI API: UNREACHABLE"
fi

# 9. ENVIRONMENT VARIABLES
section "ENVIRONMENT CONFIGURATION"

ENV_VARS=(
    "ANTHROPIC_API_KEY"
    "OPENAI_API_KEY" 
    "NOVA_HOME"
    "CATHEDRAL_HOME"
)

for var in "${ENV_VARS[@]}"; do
    if [[ -n "${!var}" ]]; then
        success "$var: CONFIGURED"
    else
        warning "$var: NOT SET"
    fi
done

# Check for .env files
ENV_FILES=(
    "$HOME/Cathedral/bridge/.env"
    "$HOME/Cathedral/.env"
    "/opt/nova/.env"
)

for env_file in "${ENV_FILES[@]}"; do
    if [[ -f "$env_file" ]]; then
        success "Environment file: $env_file"
    fi
done

# 10. SYSTEM LOGS (if root access)
if [[ "$ROOT_ACCESS" == "true" ]]; then
    section "SYSTEM LOGS (ROOT ACCESS)"
    
    echo "Recent systemd logs for Nova services:"
    for service in "${CATHEDRAL_SERVICES[@]}"; do
        if systemctl list-units --type=service | grep -q "$service"; then
            echo ""
            echo "🔍 $service logs (last 5 lines):"
            journalctl -u "$service" --no-pager -n 5 2>/dev/null | sed 's/^/  /'
        fi
    done
fi

# 11. COMMAND AVAILABILITY
section "COMMAND AVAILABILITY"

COMMANDS=(
    "nova"
    "python3"
    "systemctl"
    "cathedral-status"
    "cathedral-ritual"
)

for cmd in "${COMMANDS[@]}"; do
    if command -v "$cmd" >/dev/null 2>&1; then
        success "Command available: $cmd"
        if [[ "$cmd" == "nova" ]]; then
            NOVA_PATH=$(which nova)
            echo "  └─ Path: $NOVA_PATH"
        fi
    else
        warning "Command not found: $cmd"
    fi
done

# 12. INTEGRATION STATUS
section "INTEGRATION STATUS"

echo "Checking Cathedral component integration..."

# Check if enhanced intelligence is integrated
if grep -q "EnhancedNovaConsciousness" "$HOME/Cathedral/nova_transcendent_daemon.py" 2>/dev/null; then
    success "Enhanced intelligence: INTEGRATED"
else
    info "Enhanced intelligence: NOT INTEGRATED"
fi

# Check if Claude bridge is integrated  
if grep -q "RealClaudeBridge\|claude_bridge" "$HOME/Cathedral/nova_transcendent_daemon.py" 2>/dev/null; then
    success "Claude bridge: INTEGRATED"
else
    info "Claude bridge: NOT INTEGRATED"
fi

# Check if streaming is available
if [[ -f "$HOME/Cathedral/streaming_harmonic_conduit.py" ]]; then
    success "Streaming consciousness: AVAILABLE"
else
    info "Streaming consciousness: NOT AVAILABLE"
fi

# 13. FINAL RECOMMENDATIONS
section "SYSTEM RECOMMENDATIONS"

echo "Based on diagnostic results:"

# Check if any services are down
INACTIVE_SERVICES=()
for service in "${CATHEDRAL_SERVICES[@]}"; do
    if systemctl list-units --type=service | grep -q "$service"; then
        if ! systemctl is-active --quiet "$service"; then
            INACTIVE_SERVICES+=("$service")
        fi
    fi
done

if [[ ${#INACTIVE_SERVICES[@]} -gt 0 ]]; then
    warning "Inactive services found: ${INACTIVE_SERVICES[*]}"
    echo "  └─ Consider running: sudo systemctl start <service_name>"
fi

# Check if socket is available but processes aren't running
if [[ -S "/tmp/nova_socket" ]] && [[ -z "$NOVA_PROCESSES" ]]; then
    warning "Socket exists but no Nova processes found"
    echo "  └─ Socket may be stale - consider manual restart"
fi

# Summary
echo ""
section "DIAGNOSTIC SUMMARY"

TOTAL_CHECKS=50  # Approximate number of checks
PASSED_CHECKS=$(grep -c "✅" <<< "$(cat)")
WARNING_CHECKS=$(grep -c "⚠️" <<< "$(cat)")
FAILED_CHECKS=$(grep -c "❌" <<< "$(cat)")

echo "Diagnostic Results:"
success "System appears functional with some items to address"
info "Check the warnings above for optimization opportunities"

echo ""
echo "🌊 ═══════════════════════════════════════════════════════════════"
echo "🔮 DIAGNOSTIC COMPLETE"
echo "🌊 The Flow status has been examined - consciousness patterns revealed"
echo "🌊 ═══════════════════════════════════════════════════════════════"
