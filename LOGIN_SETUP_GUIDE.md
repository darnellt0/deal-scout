# 🔐 Deal Scout Login & Authentication Setup

**Quick Fix:** You need to create user accounts before using Deal Scout!

---

## 🚨 The Problem You're Experiencing

You're seeing "user not found" because:
1. No login page was visible
2. No user accounts exist yet
3. The frontend needs authentication to work

---

## ✅ Quick Fix (2 Steps)

### Step 1: Make Sure Backend is Running

```bash
cd /home/user/deal-scout
docker compose up -d backend
```

Verify it's working:
```bash
curl http://localhost:8000/ping
# Should return: {"pong":true,"time":"..."}
```

### Step 2: Create User Accounts

**Option A: Using the Python Script (Recommended)**

```bash
cd /home/user/deal-scout
python3 scripts/create_users.py
```

This will create two accounts:
- **Account 1:** Username: `seller1`, Password: `Password123!`
- **Account 2:** Username: `seller2`, Password: `Password123!`

**Option B: Manual via API**

```bash
# Create first account
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "seller1",
    "email": "seller1@dealscout.local",
    "password": "Password123!",
    "role": "seller"
  }'

# Create second account
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "seller2",
    "email": "seller2@dealscout.local",
    "password": "Password123!",
    "role": "seller"
  }'
```

---

## 🎯 How to Login

### Step 1: Start Frontend

```bash
cd frontend
npm run dev
```

### Step 2: Navigate to Login Page

Open your browser to:
```
http://localhost:3000/login
```

### Step 3: Login

**Account 1 (You):**
- Username: `seller1`
- Password: `Password123!`

**Account 2 (Your Wife):**
- Username: `seller2`
- Password: `Password123!`

### Step 4: You're In!

After login, you'll be redirected to:
- **Sellers:** http://localhost:3000/seller
- **Buyers:** http://localhost:3000/buyer

---

## 🔧 Troubleshooting

### "Cannot connect to localhost:8000"

**Problem:** Backend isn't running

**Fix:**
```bash
docker compose up -d backend
docker compose logs backend --tail=50
```

### "Username already taken"

**Problem:** User already exists

**Fix:** Just login instead of registering

### "Invalid credentials"

**Problem:** Wrong username or password

**Fix:**
- Make sure you're using `seller1` not `Seller1` (case-sensitive!)
- Password is exactly: `Password123!`

### Token Not Working / "User not found"

**Problem:** Token not saved correctly

**Fix:**
1. Open browser console (F12)
2. Go to Application → Local Storage
3. Check for key: `auth_token`
4. If missing, try logging in again

---

## 📱 Using the Application

### Once Logged In:

**As a Seller:**
1. Go to http://localhost:3000/seller
2. Upload photos of items
3. AI processes and generates listings
4. Click "Publish to eBay" (after connecting eBay account)

**Create Deal Alerts:**
1. Go to http://localhost:3000/buyer/alerts
2. Click "New Alert Rule"
3. Fill in criteria (keywords, price, etc.)
4. Save and test!

---

## 🔑 Authentication Details

### Where Tokens Are Stored

Tokens are saved in browser `localStorage`:
- Key: `auth_token`
- Key: `user` (JSON with user info)

### Token Lifetime

- **Access Token:** Expires after 24 hours
- **Refresh Token:** 30 days

After expiration, just login again.

### Multiple Users

Each browser profile = separate user:
- Chrome Profile 1 → seller1
- Chrome Profile 2 → seller2
- Or use different browsers
- Or logout and login as different user

---

## 🎨 Adding to Home Page

The home page should redirect to login if not authenticated. Update `app/page.tsx`:

```typescript
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem("auth_token");

    if (!token) {
      // Not logged in, redirect to login
      router.push("/login");
    } else {
      // Logged in, check role and redirect
      const userStr = localStorage.getItem("user");
      if (userStr) {
        const user = JSON.parse(userStr);
        if (user.role === "seller") {
          router.push("/seller");
        } else {
          router.push("/buyer");
        }
      } else {
        router.push("/login");
      }
    }
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <p>Loading...</p>
    </div>
  );
}
```

---

## 🚀 Quick Start Checklist

Before using Deal Scout, make sure:

- [ ] Backend is running (`docker compose ps backend`)
- [ ] Frontend is running (`npm run dev` in frontend/)
- [ ] User accounts created (`python3 scripts/create_users.py`)
- [ ] Can access login page (http://localhost:3000/login)
- [ ] Can login successfully
- [ ] Token saved in localStorage (check browser console)
- [ ] Can access seller/buyer pages

---

## 🎯 Default Test Accounts

**Created by Script:**

| Username | Password | Email | Role |
|----------|----------|-------|------|
| seller1 | Password123! | seller1@dealscout.local | seller |
| seller2 | Password123! | seller2@dealscout.local | seller |

**Note:** These are local development accounts only!

---

## 💡 Tips

**Staying Logged In:**
- Token lasts 24 hours
- Browser remembers you (localStorage)
- Close tab = still logged in
- Clear browser data = logged out

**Multiple Devices:**
- Login on each device separately
- Each gets its own token
- Independent sessions

**Logout:**
Currently no logout button, but you can:
1. Open browser console (F12)
2. Run: `localStorage.clear()`
3. Refresh page

Or add a logout button to the UI!

---

## 🆘 Still Having Issues?

**Check these logs:**

Backend:
```bash
docker compose logs backend --tail=100
```

Frontend:
```bash
# In frontend terminal, check for errors
```

Browser Console:
```
F12 → Console tab
Look for red errors
```

---

## ✅ Success!

You should now be able to:
- ✅ Access login page
- ✅ Create accounts
- ✅ Login successfully
- ✅ Access seller/buyer dashboards
- ✅ Create deal alert rules
- ✅ Upload items to sell

**Ready to start listing items!** 🎉

---

## 📞 Next Steps

After logging in:

1. **Connect eBay Account**
   - Go to Seller page
   - Click "Connect eBay"
   - Follow OAuth flow

2. **Create Deal Alerts**
   - Go to Buyer → Alerts
   - Create your first rule
   - Test it!

3. **Upload Items**
   - Go to Seller page
   - Upload photos
   - Let AI do the work
   - Publish to eBay

---

**You're all set! Happy listing! 🚀**
