#!/bin/bash
# CONSOLIDATED INSTALLER
set -e
mkdir -p /opt/nova
python3 -m venv /opt/nova/venv
source /opt/nova/venv/bin/activate
pip install --upgrade pip
pip install pyyaml psutil
cp aeon_cathedral.py /opt/nova/
cp nova_foundation.yaml /opt/nova/
sudo cp nova /usr/local/bin/
sudo chmod +x /usr/local/bin/nova
sudo cp nova-cathedral.service /etc/systemd/system/
sudo systemctl daemon-reexec
