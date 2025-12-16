#!/bin/bash
# Configure PostgreSQL to listen on Tailscale network
# Run this with sudo (requires FIDO2 authentication)

echo "⚠️  This script requires sudo access (FIDO2 tap)"
echo "Configuring PostgreSQL 16 for Tailscale network access..."
echo ""

# Backup configs
sudo cp /etc/postgresql/16/main/postgresql.conf /etc/postgresql/16/main/postgresql.conf.backup
sudo cp /etc/postgresql/16/main/pg_hba.conf /etc/postgresql/16/main/pg_hba.conf.backup

# Update listen_addresses to include Tailscale IP
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost,100.110.82.181'/" /etc/postgresql/16/main/postgresql.conf
sudo sed -i "s/listen_addresses = 'localhost'/listen_addresses = 'localhost,100.110.82.181'/" /etc/postgresql/16/main/postgresql.conf

# Add Tailscale network to pg_hba.conf
echo "" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
echo "# Tailscale VPN access (100.64.0.0/10 CGNAT range)" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf
echo "host    all             all             100.64.0.0/10           scram-sha-256" | sudo tee -a /etc/postgresql/16/main/pg_hba.conf

# Restart PostgreSQL
sudo systemctl restart postgresql@16-main

echo ""
echo "✓ PostgreSQL configured for Tailscale access"
echo "Testing connection..."
sleep 2

PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT 'Tailscale connection successful!' as status;"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Database accessible via Tailscale at 100.110.82.181:5433"
else
    echo ""
    echo "✗ Connection failed. Check firewall or Tailscale status."
fi
