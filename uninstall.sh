#!/bin/bash
echo "Uninstalling AsusCtl GUI..."
sudo rm -rf /opt/asusctl-gui
sudo rm -f /usr/share/applications/asusctl-gui.desktop
sudo rm -f /usr/share/applications/com.asus.asusctlgui.desktop
sudo update-desktop-database /usr/share/applications/ 2>/dev/null || true
echo "Done. AsusCtl GUI has been removed."