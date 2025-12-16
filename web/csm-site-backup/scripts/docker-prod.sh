#!/bin/bash

# Build production image
docker build -t complexsimplicity-prod -f Dockerfile.prod .

# Run production container
docker run -d \
  --name complexsimplicity-prod \
  -p 80:80 \
  complexsimplicity-prod