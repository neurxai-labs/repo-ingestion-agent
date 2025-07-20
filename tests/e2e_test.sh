#!/bin/bash

set -e

# Change to the root directory
cd "$(dirname "$0")/.."

# Bring up the Docker Compose services
docker-compose -f docker-compose.yml up -d

# Wait for the services to be ready
sleep 10

# Initialize a local Git repo
rm -rf /tmp/test-repo
mkdir -p /tmp/test-repo
cd /tmp/test-repo
git init
echo "test content" > test.txt
git add .
git commit -m "initial commit"

# Post to /register-repo
curl -X POST -H "Content-Type: application/json" -d '{"repo_url": "file:///tmp/test-repo", "repo_id": "test-repo"}' http://localhost:8000/register-repo

# Wait for the messages to be published
sleep 10

# Use kafka-console-consumer to read back the messages
MESSAGES=$(docker-compose exec kafka kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic repo-chunks --from-beginning --timeout-ms 5000)

# Assert the counts and content of the published chunks
EXPECTED_MESSAGE='{"repo_id": "test-repo", "file_path": "test-repo/test.txt", "offset": 0, "chunk_text": "test content\\n"}'
if [ "$MESSAGES" != "$EXPECTED_MESSAGE" ]; then
    echo "Assertion failed: Unexpected message content"
    echo "Expected: $EXPECTED_MESSAGE"
    echo "Got: $MESSAGES"
    exit 1
fi

echo "E2E test passed successfully"

# Bring down the Docker Compose services
docker-compose down