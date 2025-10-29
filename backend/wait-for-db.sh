#!/usr/bin/env sh
set -e

HOST=${DB_HOST:-postgres}
PORT=${DB_PORT:-5432}

echo "Waiting for Postgres at $HOST:$PORT..."

# Use nc (netcat) to check port availability
while ! nc -z "$HOST" "$PORT" 2>/dev/null; do
  sleep 1
done

echo "✓ Database is up and listening."
exec "$@"
