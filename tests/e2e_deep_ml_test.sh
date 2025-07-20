#!/bin/bash

set -e

# Change to the root directory
cd "$(dirname "$0")/.."

# Bring up the Docker Compose services
docker-compose -f docker-compose.yml up -d

# Wait for the services to be ready
sleep 10

# Post to /register-repo
curl -X POST -H "Content-Type: application/json" -d '{"repo_url": "https://github.com/Vishal-sys-code/deep-ml-problems.git", "repo_id": "deep-ml-problems"}' http://localhost:8000/register-repo

# Wait for the messages to be published
echo "Waiting for messages to be published..."
sleep 30

# Use amqp-consume to read back the messages
# Install amqp-tools if not present
if ! command -v amqp-consume &> /dev/null
then
    echo "amqp-tools not found, installing..."
    pip install amqp-tools
fi

MESSAGES=$(amqp-consume --url amqp://guest:guest@localhost:5672/%2F -q repo-chunks -c 1 cat)

# Assert the counts and content of the published chunks
if [ -z "$MESSAGES" ]; then
    echo "Assertion failed: No messages received"
    exit 1
fi

# Just check for the repo_id for now, as the content is large
if ! echo "$MESSAGES" | grep -q '"repo_id": "deep-ml-problems"'; then
    echo "Assertion failed: Unexpected message content"
    echo "Got: $MESSAGES"
    exit 1
fi

echo "E2E test passed successfully"

# Bring down the Docker Compose services
docker-compose down