#!/bin/bash

# Bring up the Docker Compose services
docker-compose up -d

# Wait for the services to start
sleep 10

# Fetch logs from all services
docker-compose logs --timestamps --follow
