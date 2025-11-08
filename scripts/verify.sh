#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${1:?Usage: $0 <BACKEND_URL>}"
TOKEN="${2:-}"

echo "================================"
echo "Deal Scout Verification Suite"
echo "================================"
echo "Backend: $BACKEND_URL"
echo ""

# Test 1: Ping endpoint
echo "[TEST 1] Ping endpoint..."
if curl -s "$BACKEND_URL/ping" | grep -q "pong"; then
  echo "   ✓ PASS: Backend is responding"
else
  echo "   ✗ FAIL: Backend ping failed"
  exit 1
fi
echo ""

# Test 2: Health check
echo "[TEST 2] Health check..."
HEALTH=$(curl -s "$BACKEND_URL/health" | grep -o '"ok":true' || echo "")
if [ -n "$HEALTH" ]; then
  echo "   ✓ PASS: Health check OK"
else
  echo "   ✗ FAIL: Health check failed"
fi
echo ""

# Test 3: Public listings endpoint
echo "[TEST 3] Public listings (no auth required)..."
LISTINGS=$(curl -s "$BACKEND_URL/listings?limit=5" | grep -c "id" || echo "0")
echo "   Found $LISTINGS listings"
if [ "$LISTINGS" -gt "0" ]; then
  echo "   ✓ PASS: Listings endpoint working"
fi
echo ""

# Test 4: Auth endpoint without token (should fail)
echo "[TEST 4] /auth/me without token (should fail with 401)..."
RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/auth/me" || echo "")
STATUS=$(echo "$RESPONSE" | tail -1)
if [ "$STATUS" = "401" ]; then
  echo "   ✓ PASS: Correctly rejected unauthenticated request (401)"
else
  echo "   ⚠ INFO: Got HTTP $STATUS (expected 401)"
fi
echo ""

# Test 5: If token provided, test authenticated endpoint
if [ -n "$TOKEN" ]; then
  echo "[TEST 5] /auth/me with token..."
  ME_RESPONSE=$(curl -s -X GET "$BACKEND_URL/auth/me" \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json')

  if echo "$ME_RESPONSE" | grep -q '"username"'; then
    USERNAME=$(echo "$ME_RESPONSE" | grep -o '"username":"[^"]*' | cut -d'"' -f4)
    ROLE=$(echo "$ME_RESPONSE" | grep -o '"role":"[^"]*' | cut -d'"' -f4)
    echo "   ✓ PASS: Got user info"
    echo "   Username: $USERNAME"
    echo "   Role: $ROLE"
  else
    echo "   ✗ FAIL: Could not get user info"
    echo "   Response: $ME_RESPONSE"
  fi
else
  echo "[TEST 5] SKIPPED: /auth/me (no token provided)"
  echo "   To test authenticated endpoints, run:"
  echo "   $0 $BACKEND_URL <TOKEN>"
fi
echo ""

# Test 6: Metrics endpoint
echo "[TEST 6] Metrics endpoint..."
if curl -s "$BACKEND_URL/metrics" | head -1 | grep -q "^#"; then
  echo "   ✓ PASS: Metrics endpoint available"
else
  echo "   ✗ FAIL: Metrics endpoint not responding"
fi
echo ""

echo "================================"
echo "Verification Complete"
echo "================================"
echo ""
echo "Next steps:"
echo "1. If all tests passed, deployment is successful"
echo "2. Visit frontend URL: https://deal-scout.vercel.app"
echo "3. Login should work without entering credentials (single-user mode)"
echo "4. Check browser console for any API errors"
echo ""
