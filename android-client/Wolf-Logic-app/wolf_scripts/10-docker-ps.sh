#!/bin/bash
# List running containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
