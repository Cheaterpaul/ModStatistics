#!/bin/bash

printenv | sed 's/^\(.*\)$/export \1/g' > /app/.env.sh
chmod +x /app/.env.sh

cron -f