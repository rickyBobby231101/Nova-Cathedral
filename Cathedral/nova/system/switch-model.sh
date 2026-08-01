#!/usr/bin/env bash
# Switch Nova's Ollama model without editing YAML manually.
# Usage: ./switch-model.sh gemma4:e2b
set -e

MODEL="${1:-gemma4:e2b}"
YAML="/home/daniel/nova/system/config/nova_foundation.yaml"
SERVICE="/home/daniel/nova/system/nova-cathedral.service"

echo "Switching Nova model to: $MODEL"

# Update YAML
sed -i "s/^  model: .*/  model: $MODEL/" "$YAML"

# Update service env var
sed -i "s|Environment=\"OLLAMA_MODEL=.*\"|Environment=\"OLLAMA_MODEL=$MODEL\"|" "$SERVICE"

# Reinstall service + restart daemon if running
if systemctl is-active --quiet nova-cathedral 2>/dev/null; then
    sudo cp "$SERVICE" /etc/systemd/system/nova-cathedral.service
    sudo systemctl daemon-reload
    sudo systemctl restart nova-cathedral
    echo "Daemon restarted with model: $MODEL"
else
    echo "Service not installed — config updated. Run install-services.sh to install."
fi

echo "Done. Verify with: ollama list"
