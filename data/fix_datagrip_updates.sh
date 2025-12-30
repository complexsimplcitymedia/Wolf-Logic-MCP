#!/bin/bash
# Fix DataGrip update permissions

echo "=== DataGrip Update Permission Fix ==="
echo ""
echo "Problem: DataGrip installed system-wide, can't self-update without sudo"
echo ""
echo "Solution 1: Configure polkit to allow updates without password"
echo "Solution 2: Reinstall as user-only (recommended)"
echo ""

read -p "Reinstall DataGrip as user-only? (y/n): " choice

if [[ "$choice" == "y" ]]; then
    echo ""
    echo "Removing system-wide DataGrip..."
    sudo flatpak uninstall com.jetbrains.DataGrip -y

    echo ""
    echo "Installing DataGrip for user only..."
    flatpak install --user flathub com.jetbrains.DataGrip -y

    echo ""
    echo "Setting permissions..."
    flatpak override --user com.jetbrains.DataGrip --filesystem=host:rw --share=network

    echo ""
    echo "✓ Done. DataGrip can now update itself without sudo."
    echo ""
    echo "Restart DataGrip to apply changes."
else
    echo ""
    echo "Alternative: Update manually when needed:"
    echo "  sudo flatpak update com.jetbrains.DataGrip -y"
    echo ""
    echo "Or configure polkit rule:"
    cat << 'EOF'
sudo tee /etc/polkit-1/rules.d/50-flatpak-update.rules << 'POLKIT'
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.Flatpak.app-update" &&
        subject.user == "thewolfwalksalone") {
        return polkit.Result.YES;
    }
});
POLKIT
EOF
    echo ""
fi
