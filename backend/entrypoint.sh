#!/usr/bin/env sh
set -e

# --- Config ---
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
ALEMBIC_CMD="${ALEMBIC_CMD:-python3 -m alembic upgrade head}"
PORT="${PORT:-8000}"
UVICORN_CMD="${UVICORN_CMD:-uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'}"

echo "[entrypoint] ============================================"
echo "[entrypoint] Deal-Scout Backend Entrypoint"
echo "[entrypoint] ============================================"
echo "[entrypoint]"
echo "[entrypoint] Configuration:"
echo "[entrypoint]   DB_HOST: ${DB_HOST}"
echo "[entrypoint]   DB_PORT: ${DB_PORT}"
echo "[entrypoint]   PORT: ${PORT}"
echo "[entrypoint]   ALEMBIC_CMD: ${ALEMBIC_CMD}"
echo "[entrypoint]"

# Ensure we're in app root (so alembic.ini is found)
cd /app || true

# --- Wait for DB (TCP) using Python socket, no external deps ---
echo "[entrypoint] Waiting for Postgres to accept TCP connections..."
PY_WAIT_DB="
import os, socket, time, sys
host=os.environ.get('DB_HOST','postgres')
port=int(os.environ.get('DB_PORT','5432'))
deadline=time.time()+60
ok=False
attempt=0
while time.time() < deadline:
    attempt+=1
    s=socket.socket()
    s.settimeout(2)
    try:
        s.connect((host,port))
        ok=True
        s.close()
        print(f'✓ DB reachable on attempt {attempt}', flush=True)
        break
    except Exception as e:
        elapsed=time.time()-deadline+60
        remaining=60-elapsed
        print(f'  Attempt {attempt} ({elapsed:.0f}s elapsed, {remaining:.0f}s left)... ',end='',flush=True)
        time.sleep(1)
        continue
if not ok:
    print('⚠️  DB not reachable after 60s; continuing anyway (app may start degraded)', file=sys.stderr, flush=True)
"
python3 -c "$PY_WAIT_DB" 2>&1 || true
echo "[entrypoint] DB reachability check complete."
echo "[entrypoint]"

# --- Alembic retry loop (exponential backoff) ---
echo "[entrypoint] Running database migrations..."
attempt=0
max_attempts=6
delay=2
while [ $attempt -lt $max_attempts ]; do
  attempt=$((attempt+1))
  echo "[entrypoint] Alembic attempt ${attempt}/${max_attempts} (delay: ${delay}s)..."

  if sh -lc "$ALEMBIC_CMD"; then
    echo "[entrypoint] ✓ Migrations applied successfully."
    echo "[entrypoint]"
    break
  fi

  migration_exit=$?
  echo "[entrypoint] ✗ Alembic exited with code ${migration_exit}."

  if [ $attempt -lt $max_attempts ]; then
    echo "[entrypoint] Retrying in ${delay}s..."
    sleep ${delay}
    delay=$((delay*2))
  fi
done

# --- Check if migrations completed ---
if [ $attempt -ge $max_attempts ]; then
  echo "[entrypoint] ⚠️  Migrations did not complete after ${max_attempts} attempts."
  echo "[entrypoint] WARNING: Service will start but may have incomplete schema."
  echo "[entrypoint]"
fi

# --- Start Uvicorn ---
echo "[entrypoint] Starting Uvicorn application..."
echo "[entrypoint] Command: ${UVICORN_CMD}"
echo "[entrypoint] ============================================"
echo "[entrypoint]"

exec sh -lc "$UVICORN_CMD"
