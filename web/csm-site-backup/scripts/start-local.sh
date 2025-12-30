#!/bin/bash

# Start Docker service if not running
sudo service docker status > /dev/null || sudo service docker start

# Start the application
docker-compose up