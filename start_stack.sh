#!/bin/bash

# Start LocalStack and the app
docker-compose -f docker-compose.test.yml up -d

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
sleep 15 # Adjust this delay if needed