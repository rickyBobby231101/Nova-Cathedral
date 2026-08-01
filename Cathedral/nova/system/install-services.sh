#!/usr/bin/env bash
# Install Nova Cathedral systemd services
set -e

NOVA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SYSTEMD_DIR="/etc/systemd/system"

echo "Installing Nova Cathedral services from: $NOVA_DIR"

sudo cp "$NOVA_DIR/system/nova-cathedral.service" "$SYSTEMD_DIR/"
sudo cp "$NOVA_DIR/system/nova-web.service"       "$SYSTEMD_DIR/"

sudo systemctl daemon-reload
sudo systemctl enable nova-cathedral.service nova-web.service
sudo systemctl start  nova-cathedral.service nova-web.service

echo ""
echo "Services installed and started."
echo "  Status:  systemctl status nova-cathedral nova-web"
echo "  Logs:    journalctl -fu nova-cathedral"
echo "           journalctl -fu nova-web"
echo "  Web UI:  http://localhost:5000"
