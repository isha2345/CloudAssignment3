#!/bin/bash

# Start LocalStack
docker-compose -f docker-compose.test.yml up -d localstack

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
sleep 15 # Adjust this delay if needed

# Run tests
docker-compose -f docker-compose.test.yml run test

# Clean up
docker-compose -f docker-compose.test.yml down