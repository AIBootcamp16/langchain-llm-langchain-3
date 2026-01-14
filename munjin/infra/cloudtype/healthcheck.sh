#!/bin/bash
# Health check script for FastAPI backend

set -e

# Check if the health endpoint returns 200 OK
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "Health check passed"
    exit 0
else
    echo "Health check failed with HTTP code: $HTTP_CODE"
    exit 1
fi

