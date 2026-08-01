#!/bin/bash
./install-nova-cathedral.sh
sudo systemctl start nova-cathedral
nova status
