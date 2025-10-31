# Sprint 1 - API Reference Guide

All new endpoints added in Sprint 1 (Marketplace Integrations)

---

## Authentication

All endpoints except OAuth callbacks require authentication. Include JWT token in header:
```
Authorization: Bearer {jwt_token}
```

---

## Facebook Marketplace Endpoints

### 1. Get Facebook Authorization URL

**Endpoint:** `GET /facebook/authorize`

**Authentication:** Required (JWT token)

**Description:** Generate a Facebook OAuth authorization URL. User should be redirected to this URL.

**Response:**
```json
{
  "authorization_url": "https://www.facebook.com/v18.0/dialog/oauth?...",
  "state": "secure_state_token_xyz"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/facebook/authorize" \
  -H "Authorization: Bearer {jwt_token}"
```

---

### 2. Facebook OAuth Callback

**Endpoint:** `GET /facebook/callback`

**Authentication:** Not required (OAuth callback)

**Description:** Handle the OAuth callback from Facebook. This is called automatically when user grants permissions.

**Query Parameters:**
- `code` (string, required) - Authorization code from Facebook
- `state` (string, required) - State token for CSRF protection

**Response:**
```json
{
  "success": true,
  "message": "Facebook account 'John Doe' connected successfully",
  "username": "John Doe",
  "page_id": "109234567890"
}
```

**Example:**
```
GET /facebook/callback?code=abc123...&state=xyz456...
```

---

### 3. Verify Facebook Connection

**Endpoint:** `POST /facebook/authorize`

**Authentication:** Required (JWT token)

**Description:** Check if Facebook account is connected and token is valid.

**Request Body:**
```json
{}
```

**Response (Connected):**
```json
{
  "is_connected": true,
  "is_valid": true,
  "page_id": "109234567890",
  "page_name": "John's Store",
  "connected_at": "2025-10-29T20:15:30.123456"
}
```

**Response (Not Connected):**
```json
{
  "error": "No Facebook account connected for this user"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/facebook/authorize" \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json"
```

---

### 4. Disconnect Facebook Account

**Endpoint:** `POST /facebook/disconnect`

**Authentication:** Required (JWT token)

**Description:** Disconnect your Facebook Marketplace account from Deal Scout.

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "success": true,
  "message": "Facebook account disconnected"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/facebook/disconnect" \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json"
```

---

## Offerup Marketplace Endpoints

### 1. Get Offerup Authorization URL

**Endpoint:** `GET /offerup/authorize`

**Authentication:** Required (JWT token)

**Description:** Generate an Offerup OAuth authorization URL. User should be redirected to this URL.

**Response:**
```json
{
  "authorization_url": "https://accounts.offerup.com/oauth/authorize?...",
  "state": "secure_state_token_abc"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/offerup/authorize" \
  -H "Authorization: Bearer {jwt_token}"
```

---

### 2. Offerup OAuth Callback

**Endpoint:** `GET /offerup/callback`

**Authentication:** Not required (OAuth callback)

**Description:** Handle the OAuth callback from Offerup. This is called automatically when user grants permissions.

**Query Parameters:**
- `code` (string, required) - Authorization code from Offerup
- `state` (string, required) - State token for CSRF protection

**Response:**
```json
{
  "success": true,
  "message": "Offerup account 'john_seller' connected successfully",
  "username": "john_seller",
  "user_id": "offerup_user_123"
}
```

**Example:**
```
GET /offerup/callback?code=abc123...&state=xyz456...
```

---

### 3. Verify Offerup Connection

**Endpoint:** `POST /offerup/authorize`

**Authentication:** Required (JWT token)

**Description:** Check if Offerup account is connected and token is valid.

**Request Body:**
```json
{}
```

**Response (Connected):**
```json
{
  "is_connected": true,
  "is_valid": true,
  "username": "john_seller",
  "user_id": "offerup_user_123",
  "connected_at": "2025-10-29T20:15:30.123456"
}
```

**Response (Not Connected):**
```json
{
  "error": "No Offerup account connected for this user"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/offerup/authorize" \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json"
```

---

### 4. Disconnect Offerup Account

**Endpoint:** `POST /offerup/disconnect`

**Authentication:** Required (JWT token)

**Description:** Disconnect your Offerup account from Deal Scout.

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "success": true,
  "message": "Offerup account disconnected"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/offerup/disconnect" \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json"
```

---

## Item Posting Endpoint (Enhanced)

### Post Item to Multiple Marketplaces

**Endpoint:** `POST /seller/post`

**Authentication:** Required (JWT token)

**Description:** Post an item to one or multiple marketplaces (eBay, Facebook, Offerup).

**Request Body:**
```json
{
  "item_id": 123,
  "marketplaces": ["facebook", "offerup"],
  "price": 99.99,
  "policies": {
    "listingDescription": "Custom listing description (optional)",
    "availableQuantity": 1
  }
}
```

**Response (Success):**
```json
{
  "posted": {
    "facebook": {
      "listing_id": "xyz123456",
      "url": "https://www.facebook.com/marketplace/item/xyz123456/",
      "status": "success"
    },
    "offerup": {
      "listing_id": "abc789012",
      "url": "https://www.offerup.com/item/abc789012",
      "status": "success"
    }
  }
}
```

**Response (Partial Success):**
```json
{
  "posted": {
    "facebook": {
      "listing_id": "xyz123456",
      "url": "https://www.facebook.com/marketplace/item/xyz123456/",
      "status": "success"
    },
    "offerup": {
      "status": "failed",
      "error": "Offerup account not connected. Please connect your account first."
    }
  }
}
```

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| item_id | integer | Yes | ID of the item to post |
| marketplaces | array | Yes | List of marketplaces: "facebook", "offerup", "ebay" |
| price | number | No | Override item price (uses item.price if not provided) |
| policies | object | No | Additional marketplace-specific policies |

**Error Responses:**

404 Not Found - Item not found
```json
{
  "detail": "Item not found"
}
```

400 Bad Request - Missing required fields
```json
{
  "detail": "Missing required fields"
}
```

---

## Example Workflow

### Step 1: Connect Facebook Account
```bash
# Get authorization URL
curl -X GET "http://localhost:8000/facebook/authorize" \
  -H "Authorization: Bearer {jwt_token}"

# Browser redirect to authorization_url
# User grants permissions on Facebook
# Browser redirects back to /facebook/callback
```

### Step 2: Verify Connection
```bash
curl -X POST "http://localhost:8000/facebook/authorize" \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json"
```

### Step 3: Create Item
```bash
curl -X POST "http://localhost:8000/my-items" \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Vintage Coffee Table",
    "price": 75.00,
    "description": "Beautiful wooden coffee table",
    "category": "furniture",
    "condition": "good",
    "images": ["url1", "url2"]
  }'

# Returns: {"id": 123, ...}
```

### Step 4: Post to Marketplaces
```bash
curl -X POST "http://localhost:8000/seller/post" \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": 123,
    "marketplaces": ["facebook", "offerup"],
    "price": 75.00
  }'

# Returns: {"posted": {...}}
```

---

## Error Codes

### Authentication Errors
- `401 Unauthorized` - Missing or invalid JWT token
- `403 Forbidden` - User doesn't have permission

### Not Found
- `404 Item not found` - The specified item doesn't exist
- `404 No Facebook account connected` - User hasn't connected Facebook

### Server Errors
- `500 Failed to store credentials` - Database error during OAuth
- `500 Failed to verify token` - API error verifying token

---

## Rate Limiting

No rate limiting currently implemented. Each endpoint processes requests immediately.

**Recommendations for future:**
- 10 posts per minute per user
- 5 OAuth flows per minute per user

---

## Best Practices

### 1. Always Verify Connection Before Posting
```bash
# Verify before posting
curl -X POST "http://localhost:8000/facebook/authorize" ...

# If is_valid != true, reconnect
```

### 2. Handle Partial Failures
```bash
# When posting to multiple marketplaces,
# check each marketplace's status individually

if response['posted']['facebook']['status'] == 'success':
  # Facebook post succeeded
else:
  # Facebook post failed
  # Offerup may have succeeded
```

### 3. Store Marketplace URLs
```python
# After successful posting, store the URLs
for marketplace, result in response['posted'].items():
    if result['status'] == 'success':
        store_url(item_id, marketplace, result['url'])
```

---

## OAuth Flow Diagram

```
User Clicks "Connect Facebook"
    ↓
GET /facebook/authorize
    ↓ Returns authorization_url
Browser redirects to Facebook
    ↓
User grants permissions
    ↓
Facebook redirects to GET /facebook/callback?code=...&state=...
    ↓
Backend exchanges code for token
    ↓
Token stored in MarketplaceAccount table
    ↓
✅ Account Connected
```

---

## Security Considerations

1. **State Tokens:** All OAuth flows use CSRF protection with state tokens
2. **Token Expiration:** State tokens expire after 10 minutes
3. **One-Time Use:** State tokens can only be used once
4. **Secure Storage:** Access tokens stored in database (not localStorage)
5. **Authentication:** All endpoints require JWT authentication

---

Generated: October 29, 2025
Sprint 1: Complete ✅
