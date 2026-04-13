#!/bin/bash
set -e
echo "Installing AsusCtl GUI..."
sudo mkdir -p /opt/asusctl-gui
sudo cp *.py /opt/asusctl-gui/
sudo chmod +x /opt/asusctl-gui/main.py
chmod +x uninstall.sh 2>/dev/null || true

# Pick best available icon
if [ -f "/usr/share/icons/hicolor/512x512/apps/asus_notif_blue.png" ]; then
    ICON="asus_notif_blue"
elif [ -f "/usr/share/icons/hicolor/512x512/apps/asus_notif_white.png" ]; then
    ICON="asus_notif_white"
else
    ICON="preferences-system"
fi

cat > /tmp/com.asus.asusctlgui.desktop << EOF
[Desktop Entry]
Name=AsusCtl GUI
Comment=Control ASUS laptop settings
Exec=python3 /opt/asusctl-gui/main.py
Icon=$ICON
Terminal=false
Type=Application
Categories=Settings;System;
Keywords=asus;battery;fan;gpu;performance;
StartupNotify=true
StartupWMClass=main
EOF

sudo rm -f /usr/share/applications/asusctl-gui.desktop
sudo cp /tmp/com.asus.asusctlgui.desktop /usr/share/applications/com.asus.asusctlgui.desktop
sudo chmod 644 /usr/share/applications/com.asus.asusctlgui.desktop
sudo update-desktop-database /usr/share/applications/ 2>/dev/null || true
sudo gtk-update-icon-cache -f /usr/share/icons/hicolor/ 2>/dev/null || true

echo "Done. Icon: $ICON"
echo "Launch 'AsusCtl GUI' from the application menu."