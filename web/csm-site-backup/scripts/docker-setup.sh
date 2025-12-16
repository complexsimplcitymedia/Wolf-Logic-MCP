#!/bin/bash

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add current user to docker group
sudo usermod -aG docker $USER

# Configure WSL 2
echo "[wsl2]
memory=8GB
processors=4
swap=2GB" | sudo tee /etc/wsl.conf

# Start Docker service
sudo service docker start

echo "Docker setup complete! Please restart your terminal."