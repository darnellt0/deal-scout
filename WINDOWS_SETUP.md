# Deal Scout - Windows Setup Guide

## 🚀 Quick Start for Windows Users

This guide will help you get Deal Scout running on Windows in **3 simple steps**.

---

## Prerequisites

1. **Docker Desktop** - Download and install from: https://www.docker.com/products/docker-desktop
   - After installation, make sure Docker Desktop is **running** (check system tray)

2. **Git** (optional) - For cloning the repository

---

## 🎯 Step-by-Step Setup

### Step 1: Start the Application

**Double-click:** `start-app.bat`

**OR run from Command Prompt:**
```cmd
cd C:\path\to\deal-scout
start-app.bat
```

**What it does:**
- ✅ Checks if Docker is installed and running
- ✅ Stops any existing containers
- ✅ Starts all services (database, cache, backend, frontend)
- ✅ Waits for services to be ready
- ✅ Runs database migrations automatically
- ✅ Prompts you to create a user account

**Wait time:** About 1-2 minutes for first-time startup

**Expected output:**
```
========================================
Services Started Successfully!
========================================

Backend API:  http://localhost:8000
API Docs:     http://localhost:8000/docs
Frontend UI:  http://localhost:3000
```

---

### Step 2: Create Your User Account

The `start-app.bat` script will ask if you want to create a user now.

**Option A: Create during startup (Recommended)**
- When prompted "Would you like to create a user now?", press **Y**
- Follow the prompts to enter username, email, password

**Option B: Create user later**
- Double-click: `create-user.bat`
- Follow the prompts

**What you'll need:**
- Username (e.g., "admin")
- Email (e.g., "admin@dealscout.com")
- Password (minimum 8 characters)
- First Name (optional)
- Last Name (optional)

**Success message:**
```
========================================
User Created Successfully!
========================================

You can now login at:
  http://localhost:3000
```

---

### Step 3: Access the Application

Open your web browser and go to:

**Frontend (User Interface):**
- http://localhost:3000
- Login with the username and password you created

**Backend API Documentation:**
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

---

## 📝 All Available Batch Files

### `start-app.bat` - Complete Application Startup
**What it does:**
1. Checks Docker is running
2. Starts all services
3. Runs database migrations
4. Optionally creates first user

**When to use:** First time setup or after stopping the app

---

### `create-user.bat` - Create User Accounts
**What it does:**
- Creates new user accounts via the API
- Validates backend is running
- Prompts for user details

**When to use:**
- Creating additional users
- First user creation if skipped during startup

**Example:**
```
Username: john
Email: john@example.com
Password: SecurePass123!
First Name: John
Last Name: Doe
```

---

### `run-migrations.bat` - Run Database Migrations
**What it does:**
- Shows current migration status
- Applies all pending migrations
- Updates database schema

**When to use:**
- After pulling new code changes
- When database schema needs updating
- If migrations failed during startup

**Expected output:**
```
Current migration status:
add_meta_snapjob (head)

Applying all pending migrations...
INFO  [alembic.runtime.migration] Running upgrade...
========================================
Migrations Completed Successfully!
========================================
```

---

### `stop-app.bat` - Stop All Services
**What it does:**
- Gracefully stops all Docker containers
- Preserves your data (database stays intact)

**When to use:**
- When you're done using the app
- Before shutting down your computer
- When you need to free up system resources

---

### `view-logs.bat` - View Service Logs
**What it does:**
- Shows real-time logs from services
- Helps troubleshoot issues

**Options:**
1. All services (combined logs)
2. Backend only (API logs)
3. Frontend only (UI logs)
4. Database only (PostgreSQL logs)
5. Cache only (Redis logs)

**When to use:**
- Troubleshooting errors
- Monitoring application activity
- Debugging issues

**How to exit:** Press `Ctrl+C`

---

## 🔧 Database Migrations Explained

### What are migrations?

Migrations are like **version control for your database**. They:
- Create tables (e.g., users, listings, orders)
- Add new columns to existing tables
- Modify database structure safely
- Can be rolled back if needed

### When do migrations run?

**Automatically:**
- When you run `start-app.bat` (first time)

**Manually:**
- Run `run-migrations.bat`
- Or use: `docker compose exec backend alembic upgrade head`

### Migration Commands

**Check current version:**
```cmd
docker compose exec backend alembic current
```

**View migration history:**
```cmd
docker compose exec backend alembic history
```

**Upgrade to latest:**
```cmd
docker compose exec backend alembic upgrade head
```

**Downgrade one version:**
```cmd
docker compose exec backend alembic downgrade -1
```

### Migration Files Location

All migrations are stored in:
```
backend/alembic/versions/
├── 000_create_users_table.py         ← Creates users table
├── 001_initial_schema.py              ← Creates all base tables
├── 02714c45e74e_add_missing_fields... ← Adds fields
└── ...more migration files
```

---

## 👥 Creating User Accounts

### Method 1: Batch Script (Easiest)

**Run:**
```cmd
create-user.bat
```

**Follow prompts:**
```
Username: admin
Email: admin@dealscout.com
Password: YourSecurePassword123!
First Name: Admin
Last Name: User
```

**Note:** Password will be visible on screen (limitation of Windows batch files)

---

### Method 2: Using API Directly

**With curl (if installed):**
```cmd
curl -X POST http://localhost:8000/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"email\":\"admin@dealscout.com\",\"password\":\"SecurePass123!\",\"first_name\":\"Admin\",\"last_name\":\"User\"}"
```

**With PowerShell:**
```powershell
$body = @{
    username = "admin"
    email = "admin@dealscout.com"
    password = "SecurePass123!"
    first_name = "Admin"
    last_name = "User"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/auth/register" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

---

### Method 3: Python Script (Inside Container)

```cmd
docker compose exec backend python create_admin.py
```

Follow the interactive prompts.

---

### Method 4: Direct Database Insert

**Connect to database:**
```cmd
docker compose exec postgres psql -U deals -d deals
```

**Create user with SQL:**
```sql
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
```

**Exit:** Type `\q` and press Enter

---

## 🐛 Troubleshooting

### Error: "Docker is not installed or not in PATH"

**Solution:**
1. Install Docker Desktop: https://www.docker.com/products/docker-desktop
2. Restart your computer
3. Run `start-app.bat` again

---

### Error: "Docker is not running"

**Solution:**
1. Open Docker Desktop from Start Menu
2. Wait for it to show "Docker Desktop is running"
3. Run `start-app.bat` again

---

### Error: "Port 8000 is already in use"

**Solution:**
1. Stop the other application using port 8000
2. **OR** change the port in `docker-compose.yml`:
   ```yaml
   backend:
     ports:
       - "8001:8000"  # Change 8000 to 8001
   ```

---

### Error: "User creation failed - username already exists"

**Solution:**
- Try a different username
- **OR** login with the existing username

**Check existing users:**
```cmd
docker compose exec backend python -c "from app.core.db import engine; from sqlalchemy import text; print(engine.connect().execute(text('SELECT username, email FROM users')).fetchall())"
```

---

### Error: "Cannot connect to backend"

**Check if backend is running:**
```cmd
docker compose ps
```

**Should show:**
```
NAME         SERVICE    STATUS
backend      backend    Up
frontend     frontend   Up
postgres     postgres   Up
redis        redis      Up
```

**If not running:**
```cmd
docker compose up -d
timeout /t 30
```

---

### Viewing Detailed Logs

**Run:**
```cmd
view-logs.bat
```

**Or manually:**
```cmd
REM All logs
docker compose logs -f

REM Backend only
docker compose logs -f backend

REM Last 100 lines
docker compose logs backend --tail=100
```

---

## 🔄 Common Workflows

### Daily Use
```cmd
REM Start the app
start-app.bat

REM Use the application...

REM Stop when done
stop-app.bat
```

### After Pulling New Code
```cmd
REM Stop current version
stop-app.bat

REM Pull latest code
git pull

REM Restart and run migrations
start-app.bat
```

### Creating Multiple Users
```cmd
REM First user (admin)
create-user.bat
Username: admin
...

REM Second user (buyer)
create-user.bat
Username: john
...

REM Third user (seller)
create-user.bat
Username: jane
...
```

---

## ✅ Verification Checklist

After running `start-app.bat`, verify everything works:

**1. Services Running:**
```cmd
docker compose ps
```
✅ All services should show "Up"

**2. Backend Health:**
```cmd
curl http://localhost:8000/health
```
✅ Should return: `{"status":"healthy"}`

**3. Frontend Loading:**
- Open: http://localhost:3000
✅ Should show Deal Scout interface

**4. Database Connection:**
```cmd
docker compose exec backend alembic current
```
✅ Should show current migration version

**5. User Created:**
- Try logging in at http://localhost:3000
✅ Should successfully authenticate

---

## 📊 Application URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Main user interface |
| Backend API | http://localhost:8000 | REST API |
| API Docs (Swagger) | http://localhost:8000/docs | Interactive API documentation |
| API Docs (ReDoc) | http://localhost:8000/redoc | Alternative API docs |
| Health Check | http://localhost:8000/health | Service health status |
| Metrics | http://localhost:8000/metrics | Prometheus metrics |

---

## 🎓 Next Steps

After successful setup:

1. **Explore the application:**
   - Login at http://localhost:3000
   - Check out the buyer dashboard
   - Try the seller features

2. **Configure API keys** (optional):
   - Edit `.env` file
   - Add your OpenAI API key for AI features
   - Add eBay credentials for marketplace integration

3. **Create more users:**
   - Run `create-user.bat` multiple times
   - Test different user roles (buyer, seller, admin)

4. **Read the documentation:**
   - See `QUICK_START.md` for detailed info
   - Check `README.md` for project overview

---

## 💡 Tips

**Faster Startup:**
- Keep Docker Desktop running in the background
- First startup is slower (downloads images)
- Subsequent startups are much faster (~30 seconds)

**Data Persistence:**
- Your data is saved even when you stop the app
- Database is stored in a Docker volume
- To completely reset: `docker compose down -v` (⚠️ deletes all data)

**Development:**
- Edit code while app is running
- Backend auto-reloads on file changes
- Frontend hot-reloads automatically
- No need to restart containers for code changes

---

## 🆘 Getting Help

**View logs for errors:**
```cmd
view-logs.bat
```

**Check service status:**
```cmd
docker compose ps
```

**Restart a specific service:**
```cmd
docker compose restart backend
```

**Complete reset:**
```cmd
docker compose down -v
start-app.bat
```

**Still stuck?**
- Check the logs in `view-logs.bat`
- Review error messages carefully
- Consult `QUICK_START.md` for more details

---

**Happy Deal Scouting! 🎉**
