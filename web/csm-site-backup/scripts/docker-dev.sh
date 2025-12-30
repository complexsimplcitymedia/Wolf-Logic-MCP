#!/bin/bash

# Build and start containers
docker-compose up --build -d

# Watch logs
docker-compose logs -f