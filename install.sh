#!/bin/bash
# PenKit TUI - Kali Linux Setup
set -e

echo "[*] Installing Python dependencies..."
pip3 install -r requirements.txt

echo "[*] Checking required tools..."
TOOLS="airmon-ng airodump-ng aireplay-ng aircrack-ng hcxdumptool hcxpcapngtool hostapd dnsmasq hashcat john"
MISSING=()

for tool in $TOOLS; do
    if ! command -v "$tool" &>/dev/null; then
        MISSING+=("$tool")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "[!] Missing tools: ${MISSING[*]}"
    echo "[*] Installing via apt..."
    apt-get install -y aircrack-ng hcxdumptool hcxtools hostapd dnsmasq hashcat john 2>/dev/null || true
fi

echo "[*] Ensuring output directory exists..."
mkdir -p ~/penkit-captures

echo ""
echo "[+] Setup complete!"
echo "[+] Run with: sudo python3 main.py"
echo ""
echo "    Keyboard shortcuts:"
echo "    1 / 2 / 3  - Switch tabs"
echo "    ?          - Help panel"
echo "    q          - Quit"
