#!/bin/bash

# Stop any running containers
docker-compose down

# Build and start containers in detached mode
docker-compose up --build -d

# Wait for container to be ready
echo "Waiting for container to be ready..."
sleep 5

# Show container status
docker-compose ps

echo "Local deployment complete!"
echo "Your site is now available at http://localhost:3000"