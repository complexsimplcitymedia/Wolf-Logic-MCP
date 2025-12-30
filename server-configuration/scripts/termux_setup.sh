#!/data/data/com.termux/files/usr/bin/bash
echo "Initializing Wolf Node - S24 Ultra..."
# Update repositories
pkg update -y
pkg upgrade -y

# Install Core Tools
pkg install -y python git openssh vim curl wget

# Install Network Analysis Tools
pkg install -y net-tools nmap traceroute dnsutils

# Install Python Security Libraries
pip install requests scapy

echo "Wolf Node Ready. System is Green."
