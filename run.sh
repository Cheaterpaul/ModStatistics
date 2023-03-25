#!/bin/bash

source /app/.env.sh

python3 /app/main.py > /proc/$(cat /var/run/crond.pid)/fd/1 2>&1