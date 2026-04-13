#!/bin/bash
sudo rm -rf /opt/asusctl-gui
sudo rm -f /usr/share/applications/asusctl-gui.desktop
sudo update-desktop-database /usr/share/applications/ 2>/dev/null || true
echo "ASUS Control Center uninstalled."
