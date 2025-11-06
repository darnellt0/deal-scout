# eBay Cross-Posting Integration Guide

Complete guide for implementing and using the eBay cross-posting feature in Deal Scout.

---

## Overview

This implementation provides end-to-end eBay integration with:
- OAuth 2.0 authentication flow
- Automatic token refresh
- Inventory item management
- Offer creation and publishing
- Category suggestion and aspect validation
- Policy and location management

---

## Architecture

### Components

1. **Database Tables**
   - `seller_integrations`: Stores OAuth tokens and eBay configuration
   - `crosspost_results`: Tracks published listings

2. **eBay Client** (`app/integrations/ebay/client.py`)
   - OAuth token exchange and refresh
   - Inventory API calls
   - Taxonomy API (categories and aspects)
   - Account policies API

3. **API Routes**
   - `/integrations/ebay/connect`: Get OAuth consent URL
   - `/integrations/ebay/callback`: Handle OAuth callback
   - `/integrations/ebay/bootstrap`: Set up policies and location
   - `/integrations/ebay/publish/{listing_id}`: Publish to eBay
   - `/integrations/ebay/status`: Check integration status

---

## Setup Instructions

### 1. Environment Configuration

Your `.env` file should have:

```bash
EBAY_ENV=sandbox  # or 'production'
EBAY_CLIENT_ID=your_client_id
EBAY_CLIENT_SECRET=your_client_secret
EBAY_REDIRECT_URI=http://localhost:8000/integrations/ebay/callback
EBAY_MARKETPLACE_ID=EBAY_US
```

### 2. Run Database Migration

```bash
# From backend directory
cd backend

# Run migration
alembic upgrade head
```

This creates the `seller_integrations` and `crosspost_results` tables.

### 3. Start the Application

```bash
# Start backend
docker compose up -d backend

# Verify
curl http://localhost:8000/health
```

---

## Usage Workflow

### Step 1: Connect eBay Account

**Get Consent URL:**
```bash
curl -X GET http://localhost:8000/integrations/ebay/connect \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "consent_url": "https://auth.sandbox.ebay.com/oauth2/authorize?...",
  "provider": "ebay",
  "message": "Redirect user to this URL to authorize eBay access"
}
```

**Action:** Redirect user to `consent_url` in browser.

### Step 2: Handle OAuth Callback

After user grants permission, eBay redirects to:
```
http://localhost:8000/integrations/ebay/callback?code=XXXXX&state=user_123
```

The backend automatically exchanges the code for tokens and saves them.

**Response:**
```json
{
  "success": true,
  "provider": "ebay",
  "message": "Successfully connected eBay account. Run /bootstrap to complete setup.",
  "integration_id": 1
}
```

### Step 3: Bootstrap Integration

This sets up policies and inventory location:

```bash
curl -X POST http://localhost:8000/integrations/ebay/bootstrap \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**What it does:**
1. Fetches your eBay payment, fulfillment, and return policies
2. Selects default policies (first of each type)
3. Creates default inventory location
4. Saves configuration

**Response:**
```json
{
  "success": true,
  "payment_policy_id": "12345",
  "fulfillment_policy_id": "67890",
  "return_policy_id": "54321",
  "location_key": "DEFAULT_1",
  "marketplace_id": "EBAY_US",
  "message": "eBay integration fully configured and ready to use"
}
```

### Step 4: Publish a Listing

```bash
curl -X POST http://localhost:8000/integrations/ebay/publish/123 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**What it does:**
1. Loads your eBay integration (tokens, policies)
2. Loads Deal Scout listing #123
3. Suggests eBay category from title
4. Validates required aspects
5. Creates inventory item
6. Creates offer
7. Publishes to eBay
8. Returns eBay URL

**Response:**
```json
{
  "success": true,
  "provider": "ebay",
  "listing_id": 123,
  "offer_id": "1234567890",
  "item_id": "v1|123456|0",
  "url": "https://www.sandbox.ebay.com/itm/v1|123456|0",
  "message": "Successfully published to eBay"
}
```

### Step 5: Check Status

```bash
# Check integration status
curl -X GET http://localhost:8000/integrations/ebay/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check specific listing
curl -X GET http://localhost:8000/integrations/ebay/listings/123/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Error Handling

### 400: Not Connected
```json
{
  "error": "eBay not connected",
  "action": "Connect your eBay account at /integrations/ebay/connect"
}
```
**Fix:** User needs to go through OAuth flow.

### 400: Not Bootstrapped
```json
{
  "error": "eBay integration not fully configured",
  "action": "Run /integrations/ebay/bootstrap to complete setup"
}
```
**Fix:** Call `/bootstrap` endpoint.

### 401: Token Expired
```json
{
  "error": "eBay authentication expired",
  "action": "Re-connect your eBay account at /integrations/ebay/connect"
}
```
**Fix:** User needs to re-authenticate.

### 422: Missing Aspects
```json
{
  "error": "Missing required aspects",
  "missing_aspects": [
    {
      "name": "Brand",
      "required": true,
      "values": ["Nike", "Adidas", "Other"]
    },
    {
      "name": "Size",
      "required": true,
      "values": ["Small", "Medium", "Large"]
    }
  ],
  "category_id": "12345",
  "action": "Add required aspects to listing before publishing"
}
```
**Fix:** Add required fields to listing and retry.

---

## Data Mapping

### Listing → eBay Inventory Item

| Deal Scout | eBay Field | Notes |
|------------|-----------|-------|
| `title` | `product.title` | Max 80 chars |
| `description` | `product.description` | Full description |
| `price` | `pricingSummary.price.value` | USD format |
| `condition` | `condition` | Mapped (see table below) |
| `thumbnail_url` | `product.imageUrls[0]` | Must be HTTPS |

### Condition Mapping

| Deal Scout | eBay Condition |
|------------|----------------|
| excellent | USED_EXCELLENT |
| great | USED_VERY_GOOD |
| good | USED_GOOD |
| fair | USED_ACCEPTABLE |
| poor | FOR_PARTS_OR_NOT_WORKING |

---

## Testing

### Unit Tests

Create `backend/tests/test_ebay_integration.py`:

```python
import pytest
from app.integrations.ebay import EbayClient


@pytest.mark.asyncio
async def test_build_consent_url():
    """Test consent URL generation."""
    client = EbayClient(env="sandbox")
    url = client.build_consent_url(state="test_state")

    assert "auth.sandbox.ebay.com" in url
    assert "client_id=" in url
    assert "state=test_state" in url


@pytest.mark.asyncio
async def test_token_exchange_invalid_code():
    """Test token exchange with invalid code."""
    client = EbayClient(env="sandbox")

    with pytest.raises(Exception):
        await client.exchange_code_for_tokens("invalid_code")
```

### Integration Tests (Sandbox)

```python
import pytest
from app.integrations.ebay import EbayClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_publish_flow():
    """Test full publish flow with sandbox."""
    # This requires valid sandbox credentials
    # Skip in CI: pytest -m "not integration"
    pass
```

Run tests:
```bash
# Unit tests only
pytest backend/tests/test_ebay_integration.py

# Include integration tests
pytest backend/tests/test_ebay_integration.py -m integration
```

---

## Postman Collection

Import `Deal-Scout-eBay.postman_collection.json`:

```json
{
  "info": {
    "name": "Deal Scout - eBay Integration",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "1. Get Consent URL",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/integrations/ebay/connect",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ]
      }
    },
    {
      "name": "2. OAuth Callback",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{base_url}}/integrations/ebay/callback?code={{auth_code}}&state={{state}}",
          "query": [
            {"key": "code", "value": "{{auth_code}}"},
            {"key": "state", "value": "{{state}}"}
          ]
        }
      }
    },
    {
      "name": "3. Bootstrap Integration",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/integrations/ebay/bootstrap",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ]
      }
    },
    {
      "name": "4. Publish Listing",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/integrations/ebay/publish/{{listing_id}}",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ]
      }
    },
    {
      "name": "5. Check Status",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/integrations/ebay/status",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ]
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    },
    {
      "key": "access_token",
      "value": "your_jwt_token"
    },
    {
      "key": "listing_id",
      "value": "1"
    }
  ]
}
```

---

## Frontend Integration (Next Steps)

### Add "Connect eBay" Button

```typescript
// components/EbayConnectButton.tsx
"use client";

import { useState } from "react";

export function EbayConnectButton() {
  const [loading, setLoading] = useState(false);

  const handleConnect = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/integrations/ebay/connect", {
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
      });
      const data = await response.json();

      // Redirect to eBay consent page
      window.location.href = data.consent_url;
    } catch (error) {
      console.error("Failed to connect eBay:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleConnect}
      disabled={loading}
      className="btn btn-primary"
    >
      {loading ? "Connecting..." : "Connect eBay Account"}
    </button>
  );
}
```

### Handle OAuth Callback

```typescript
// app/integrations/ebay/callback/page.tsx
"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function EbayCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");

    if (code) {
      // Backend will handle this automatically via GET /callback
      // Just bootstrap the integration
      fetch("/api/integrations/ebay/bootstrap", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`,
        },
      })
        .then(() => router.push("/seller?ebay_connected=true"))
        .catch((error) => {
          console.error("Bootstrap failed:", error);
          router.push("/seller?ebay_error=true");
        });
    }
  }, [searchParams, router]);

  return <div>Connecting eBay account...</div>;
}
```

### Add "Publish to eBay" Button

```typescript
// components/PublishToEbayButton.tsx
"use client";

import { useState } from "react";

interface Props {
  listingId: number;
}

export function PublishToEbayButton({ listingId }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handlePublish = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/integrations/ebay/publish/${listingId}`,
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail.error || "Failed to publish");
      }

      const data = await response.json();
      setResult(data);

      // Open eBay listing in new tab
      window.open(data.url, "_blank");
    } catch (error) {
      console.error("Failed to publish:", error);
      alert(`Failed to publish: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button
        onClick={handlePublish}
        disabled={loading}
        className="btn btn-success"
      >
        {loading ? "Publishing..." : "Publish to eBay"}
      </button>

      {result && (
        <div className="alert alert-success mt-2">
          Successfully published!
          <a href={result.url} target="_blank" rel="noopener">
            View on eBay
          </a>
        </div>
      )}
    </div>
  );
}
```

---

## Production Deployment

### Environment Variables

Set in production `.env`:

```bash
EBAY_ENV=production
EBAY_CLIENT_ID=production_client_id
EBAY_CLIENT_SECRET=production_client_secret
EBAY_REDIRECT_URI=https://yourdomain.com/integrations/ebay/callback
EBAY_MARKETPLACE_ID=EBAY_US
```

### Security Considerations

1. **HTTPS Required**: eBay requires HTTPS for redirect URIs in production
2. **Token Storage**: Access tokens stored encrypted in database
3. **CSRF Protection**: State parameter validates OAuth callbacks
4. **Token Refresh**: Automatic refresh before expiration
5. **Rate Limiting**: eBay has rate limits - implement caching

### Monitoring

Add logging for:
- OAuth connection attempts
- Token refresh events
- Publish successes/failures
- API errors

Example:
```python
logger.info(f"User {user_id} connected eBay account")
logger.info(f"Published listing {listing_id} to eBay: {ebay_url}")
logger.error(f"Failed to publish listing {listing_id}: {error}")
```

---

## Troubleshooting

### "No policies found"

**Problem:** Bootstrap fails because seller hasn't created eBay policies.

**Solution:** Create policies in [eBay Seller Hub](https://www.ebay.com/sh/ovw):
1. Go to Account → Business Policies
2. Create Payment Policy
3. Create Shipping Policy (Fulfillment)
4. Create Return Policy

### "Category not found"

**Problem:** eBay can't suggest a category for the listing.

**Solution:** Improve listing title to be more descriptive, or manually specify category ID.

### "Missing required aspects"

**Problem:** Category requires specific attributes (Brand, Size, etc.).

**Solution:** Add fields to your listing model and map them to eBay aspects.

### "401 Unauthorized" errors

**Problem:** Access token expired.

**Solution:** The client automatically refreshes tokens, but user may need to re-authorize if refresh token also expired.

---

## Next Steps

1. **Add frontend UI** - Connect button, publish button, status indicators
2. **Implement aspects mapping** - Intelligent mapping of listing attributes to eBay aspects
3. **Add bulk publishing** - Publish multiple listings at once
4. **Implement listing sync** - Sync status, views, watchers from eBay
5. **Add order management** - Handle sales, shipping, tracking
6. **Implement repricing** - Automatic price adjustments based on eBay data

---

## API Documentation

Full API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Filter by tag: `ebay-integration` and `ebay-publish`

---

## Support

For issues or questions:
1. Check logs: `docker compose logs -f backend`
2. Test with Postman collection
3. Verify eBay credentials in Developer Portal
4. Check database for integration record

---

**Implementation Complete! ✅**

You now have a fully functional eBay cross-posting system. Start with the sandbox environment, test thoroughly, then switch to production when ready.
