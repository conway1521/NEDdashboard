#!/bin/bash

# Wait for 5 minutes
sleep 300

# Force kill anything on port 8061
lsof -ti:8061 | xargs kill -9

# Exit
exit 0