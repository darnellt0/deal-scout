# Deal Scout - Quick Start Guide

## 🚀 Getting Your Application Running

After the diagnostic fixes, follow these steps to get the application fully operational.

---

## Prerequisites

- Docker and Docker Compose installed
- Port 8000 (backend) and 3000 (frontend) available

---

## Step 1: Start the Services

```bash
# From the project root directory
cd /path/to/deal-scout

# Start all services (database, redis, backend, frontend)
docker compose up -d

# Watch the logs to ensure services start successfully
docker compose logs -f
```

**Expected output:**
- `postgres` - Database ready
- `redis` - Redis server running
- `backend` - FastAPI application started
- `frontend` - Next.js application ready

**Wait 30 seconds** for all services to fully initialize.

---

## Step 2: Run Database Migrations

The users table migration we created needs to be applied:

```bash
# Run migrations
docker compose exec backend alembic upgrade head

# Verify migrations succeeded
docker compose exec backend alembic current
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade  -> 000_create_users_table, create users table
INFO  [alembic.runtime.migration] Running upgrade 000_create_users_table -> 001_initial_schema, Initial schema creation
...
Current revision: add_meta_snapjob (head)
```

---

## Step 3: Create Your First User

There are **3 ways** to create a user:

### Option A: Using the Setup Endpoint (Recommended)

```bash
curl -X POST http://localhost:8000/setup/create-demo-user \
  -H "Content-Type: application/json"
```

### Option B: Using the Registration API

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@dealscout.com",
    "password": "ChangeMe123!",
    "first_name": "Admin",
    "last_name": "User"
  }'
```

### Option C: Create User via Database

```bash
# Connect to the database
docker compose exec postgres psql -U deals -d deals

# In psql, run:
INSERT INTO users (username, email, password_hash, role, is_active, is_verified, created_at, updated_at)
VALUES (
  'admin',
  'admin@dealscout.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oo2IQ/hqo7iC',  -- password: "password"
  'admin',
  true,
  true,
  NOW(),
  NOW()
);

# Exit psql
\q
```

---

## Step 4: Verify Application is Working

### Test Backend

```bash
# Health check
curl http://localhost:8000/health

# List users (should now show your user)
curl http://localhost:8000/auth/users
```

### Test Frontend

Open your browser to: **http://localhost:3000**

You should now see the Deal Scout application with a login screen.

### Test Login

```bash
# Login to get JWT token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'
```

**Expected response:**
```json
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer"
}
```

---

## Step 5: Access the Application

### Frontend (User Interface)
- **URL:** http://localhost:3000
- **Login:** Use the credentials you created

### Backend API Docs
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Health & Metrics
- **Health Check:** http://localhost:8000/health
- **Metrics:** http://localhost:8000/metrics

---

## 🐛 Troubleshooting

### "User not found" error

**Cause:** No users exist in the database

**Fix:** Follow Step 3 above to create a user

---

### Services won't start

```bash
# Check service status
docker compose ps

# View logs for specific service
docker compose logs backend
docker compose logs frontend
docker compose logs postgres

# Restart a service
docker compose restart backend
```

---

### Database connection errors

```bash
# Verify database is running
docker compose exec postgres pg_isready -U deals

# Check database exists
docker compose exec postgres psql -U deals -l

# Recreate database (WARNING: deletes all data)
docker compose down -v
docker compose up -d
# Then run migrations again (Step 2)
```

---

### Migration errors

```bash
# Check current migration state
docker compose exec backend alembic current

# View migration history
docker compose exec backend alembic history

# Downgrade one migration
docker compose exec backend alembic downgrade -1

# Upgrade to latest
docker compose exec backend alembic upgrade head
```

---

### Port already in use

```bash
# Find what's using port 8000
lsof -i :8000
# or
netstat -tulpn | grep :8000

# Kill the process or change port in docker-compose.yml
```

---

## 🔧 Development Mode

For local development without Docker:

### Backend

```bash
cd backend

# Install dependencies
pip install -e ".[dev]"

# Set environment variables
export DATABASE_URL="postgresql+psycopg://deals:deals@localhost:5432/deals"
export REDIS_URL="redis://localhost:6379/0"

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies (already done)
npm install

# Start development server
npm run dev
```

---

## 📊 Verify Everything Works

Run this comprehensive test:

```bash
#!/bin/bash
echo "🔍 Checking Deal Scout services..."

echo -n "Backend health: "
curl -s http://localhost:8000/health | jq -r '.status' || echo "❌ FAILED"

echo -n "Frontend: "
curl -s http://localhost:3000 > /dev/null && echo "✅ OK" || echo "❌ FAILED"

echo -n "Database: "
docker compose exec -T postgres pg_isready -U deals -q && echo "✅ OK" || echo "❌ FAILED"

echo -n "Redis: "
docker compose exec -T redis redis-cli ping | grep -q PONG && echo "✅ OK" || echo "❌ FAILED"

echo -n "Migrations: "
docker compose exec -T backend alembic current | grep -q "head" && echo "✅ OK" || echo "⚠️  Not at head"

echo "✅ All checks complete!"
```

---

## 🎯 Next Steps After Startup

1. **Change default passwords** - Update admin password immediately
2. **Configure API keys** - Set OpenAI, eBay, etc. in `.env`
3. **Test features** - Try creating listings, running searches
4. **Review logs** - Check for any warnings or errors

---

## 📝 Summary of What Was Fixed

The diagnostic workup fixed these **15 critical issues**:

✅ Created missing backend/static directory
✅ Installed missing Python dependencies
✅ Fixed malformed config.py
✅ Created users table migration
✅ Fixed useState bug in frontend
✅ Configured environment variables
✅ Applied rate limiting middleware
✅ Fixed CI/CD pipeline
✅ And 7 more critical fixes...

**But you still need to:**
1. ✅ Start the services
2. ✅ Run migrations
3. ✅ Create a user

---

## 🆘 Still Having Issues?

Check the detailed diagnostic reports or run:

```bash
docker compose logs backend | tail -100
docker compose logs frontend | tail -100
```

Look for specific error messages and search the diagnostic reports for solutions.
