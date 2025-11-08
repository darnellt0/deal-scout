#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${1:?Usage: $0 <BACKEND_URL>}"

# Configuration
USERNAME="darnell"
EMAIL="darnell.tomlinson@gmail.com"
PASSWORD="tomlinson"

echo "================================"
echo "Deal Scout User Seed Script"
echo "================================"
echo "Backend: $BACKEND_URL"
echo "Username: $USERNAME"
echo ""

# Step 1: Register user (ignore 409 Conflict if already exists)
echo "[1/3] Registering user..."
REGISTER_RESPONSE=$(curl -s -X POST "$BACKEND_URL/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$USERNAME\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  2>/dev/null || echo '{"error":"register failed"}')

if echo "$REGISTER_RESPONSE" | grep -q '"error"'; then
  if echo "$REGISTER_RESPONSE" | grep -q '409\|already exists'; then
    echo "   ✓ User already exists (409) — proceeding"
  else
    echo "   ⚠ Register response: $REGISTER_RESPONSE"
  fi
else
  echo "   ✓ User registered"
fi

# Step 2: Login to get JWT token
echo "[2/3] Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4 || echo "")

if [ -z "$TOKEN" ]; then
  echo "   ✗ FAILED to get token. Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "   ✓ Got JWT token"
echo ""
echo "TOKEN=$TOKEN"
echo ""

# Step 3: Check identity (should show seller role)
echo "[3/3] Checking user identity..."
ME_RESPONSE=$(curl -s -X GET "$BACKEND_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json')

echo "   Response: $ME_RESPONSE"
echo ""

ROLE=$(echo "$ME_RESPONSE" | grep -o '"role":"[^"]*' | cut -d'"' -f4 || echo "unknown")

if [ "$ROLE" = "seller" ]; then
  echo "✓ SUCCESS: User is seller. Ready to deploy!"
else
  echo "⚠ WARNING: Role is '$ROLE', not 'seller'. You may need to promote the user."
  echo ""
  echo "To promote via SQL, run on Neon:"
  echo "  UPDATE users SET role='seller', is_verified=true WHERE username='$USERNAME';"
  echo ""
  echo "Then log in again to get a new token with seller role."
fi

echo ""
echo "================================"
echo "Next steps:"
echo "1. Save the TOKEN above"
echo "2. Copy to browser console:"
echo "   localStorage.setItem('access_token', '$TOKEN');"
echo "   location.reload();"
echo "================================"
