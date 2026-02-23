#!/bin/bash

# Ensure we are in the correct directory
cd "$(dirname "$0")"

# Log start time
echo "----------------------------------------" >> vinotifier.log
echo "Starting Vinotifier at $(date)" >> vinotifier.log

# Run the container
# Using the full path to docker-compose is safer for cron
# If docker-compose is not in PATH, you might need to specify it (e.g. /usr/local/bin/docker-compose)
docker-compose up >> vinotifier.log 2>&1

# Log end time
echo "Finished Vinotifier at $(date)" >> vinotifier.log
echo "----------------------------------------" >> vinotifier.log
