# Phase 6 - Sprint 1: Marketplace Integrations (Week 1)

**Sprint Goal:** Enable sellers to post items to Facebook Marketplace and Offerup
**Duration:** 5 days (Mon-Fri)
**Team Size:** 1-2 developers
**Deliverables:** Facebook & Offerup OAuth + Item posting + Webhooks

---

## Task Breakdown

### Day 1: Facebook Marketplace OAuth (Dev 1)

#### Task 1.1: Create Facebook OAuth Route Handler
**File:** `backend/app/routes/facebook_oauth.py`
**Lines:** ~150
**Time:** 2-3 hours

```python
"""Facebook Marketplace OAuth flow."""

from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
from app.core.auth import get_current_user
from app.core.db import SessionLocal
from app.core.models import User, MarketplaceAccount
from app.config import get_settings

router = APIRouter(prefix="/facebook", tags=["facebook-oauth"])

@router.get("/authorize")
async def facebook_authorize(
    current_user: User = Depends(get_current_user),
):
    """
    Generate Facebook OAuth authorization URL.
    User should be redirected to this URL to start OAuth flow.
    """
    settings = get_settings()

    auth_url = "https://www.facebook.com/v12.0/dialog/oauth"
    params = {
        "client_id": settings.facebook_app_id,
        "redirect_uri": f"{settings.backend_url}/facebook/callback",
        "scope": "pages_manage_metadata,pages_read_engagement,pages_manage_posts,pages_manage_engagement",
        "state": generate_state_token(current_user.id),
    }

    url = f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    return {"authorization_url": url}


@router.get("/callback")
async def facebook_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Handle OAuth callback from Facebook.
    Exchange code for access token and store in database.
    """
    settings = get_settings()

    # Verify state token
    user_id = verify_state_token(state)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid state token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Exchange code for access token
    token_url = "https://graph.facebook.com/v12.0/oauth/access_token"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            params={
                "client_id": settings.facebook_app_id,
                "client_secret": settings.facebook_app_secret,
                "redirect_uri": f"{settings.backend_url}/facebook/callback",
                "code": code,
            },
        )
        response.raise_for_status()
        token_data = response.json()

    access_token = token_data["access_token"]

    # Get user's Facebook pages
    pages_url = "https://graph.facebook.com/me/accounts"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            pages_url,
            params={"access_token": access_token}
        )
        response.raise_for_status()
        pages = response.json()["data"]

    # Store first page as default (user should be able to select)
    if pages:
        page = pages[0]

        # Check if account already exists
        existing = db.query(MarketplaceAccount).filter(
            MarketplaceAccount.user_id == user.id,
            MarketplaceAccount.marketplace == "facebook"
        ).first()

        if existing:
            existing.marketplace_account_id = page["id"]
            existing.account_username = page["name"]
            existing.access_token = access_token
            existing.is_active = True
        else:
            account = MarketplaceAccount(
                user_id=user.id,
                marketplace="facebook",
                marketplace_account_id=page["id"],
                account_username=page["name"],
                access_token=access_token,
                is_active=True,
            )
            db.add(account)

        db.commit()

        return {
            "success": True,
            "message": "Facebook account connected",
            "page_name": page["name"],
            "page_id": page["id"],
        }

    raise HTTPException(
        status_code=400,
        detail="No Facebook pages found. Create a page first.",
    )


@router.post("/authorize")
async def verify_facebook_connection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify Facebook connection is valid.
    Useful for testing or checking if token is expired.
    """
    account = db.query(MarketplaceAccount).filter(
        MarketplaceAccount.user_id == current_user.id,
        MarketplaceAccount.marketplace == "facebook"
    ).first()

    if not account or not account.access_token:
        raise HTTPException(
            status_code=404,
            detail="No Facebook account connected"
        )

    # Verify token is still valid
    debug_url = "https://graph.facebook.com/debug_token"
    settings = get_settings()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            debug_url,
            params={
                "input_token": account.access_token,
                "access_token": f"{settings.facebook_app_id}|{settings.facebook_app_secret}"
            }
        )

    if response.status_code == 200:
        token_info = response.json()["data"]
        return {
            "is_valid": token_info["is_valid"],
            "app_id": token_info["app_id"],
            "user_id": token_info.get("user_id"),
        }

    raise HTTPException(status_code=400, detail="Token verification failed")


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Checklist:**
- [ ] Create `backend/app/routes/facebook_oauth.py`
- [ ] Implement authorize endpoint
- [ ] Implement callback handler
- [ ] Implement token verification
- [ ] Add state token generation/verification
- [ ] Add to `backend/app/main.py` router

---

#### Task 1.2: Create Facebook Client for API Calls
**File:** `backend/app/market/facebook_client.py`
**Lines:** ~200
**Time:** 2-3 hours

```python
"""Facebook Marketplace API client."""

import httpx
import logging
from typing import Dict, List, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)


class FacebookMarketplaceClient:
    """Client for Facebook Marketplace API."""

    def __init__(self, access_token: str, page_id: str):
        """Initialize with access token and page ID."""
        self.access_token = access_token
        self.page_id = page_id
        self.base_url = "https://graph.facebook.com/v12.0"

    async def post_item(
        self,
        title: str,
        description: str,
        price: float,
        images: List[str],
        category: str,
        condition: str = "USED",
    ) -> Optional[str]:
        """
        Post an item to Facebook Marketplace.

        Args:
            title: Item title
            description: Item description
            price: Item price in dollars
            images: List of image URLs
            category: Facebook Marketplace category
            condition: Item condition (USED, LIKE_NEW, NEW)

        Returns:
            Facebook marketplace listing ID
        """
        try:
            # Upload images first
            photo_ids = []
            for image_url in images:
                photo_id = await self._upload_photo(image_url)
                if photo_id:
                    photo_ids.append(photo_id)

            # Create marketplace listing
            url = f"{self.base_url}/{self.page_id}/feed"
            payload = {
                "message": f"{title}\n\n{description}",
                "type": "MARKETPLACE_LISTING",
                "marketplace_listing": {
                    "name": title,
                    "description": description,
                    "price_currency": "USD",
                    "price_amount": int(price * 100),  # Cents
                    "category_specific_fields": {
                        "category": category,
                        "condition": condition,
                    },
                    "photo_ids": photo_ids,
                },
                "access_token": self.access_token,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

            result = response.json()
            listing_id = result.get("id")

            logger.info(f"Item posted to Facebook: {listing_id}")
            return listing_id

        except Exception as e:
            logger.error(f"Failed to post item to Facebook: {e}")
            return None

    async def _upload_photo(self, image_url: str) -> Optional[str]:
        """Upload photo to Facebook."""
        try:
            url = f"{self.base_url}/{self.page_id}/photos"

            payload = {
                "url": image_url,
                "access_token": self.access_token,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=payload)
                response.raise_for_status()

            result = response.json()
            return result.get("id")

        except Exception as e:
            logger.error(f"Failed to upload photo: {e}")
            return None

    async def update_item(
        self,
        listing_id: str,
        **kwargs
    ) -> bool:
        """Update item details."""
        try:
            url = f"{self.base_url}/{listing_id}"

            payload = {
                "access_token": self.access_token,
                **kwargs
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

            logger.info(f"Item updated on Facebook: {listing_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update item: {e}")
            return False

    async def delete_item(self, listing_id: str) -> bool:
        """Delete item from Facebook Marketplace."""
        try:
            url = f"{self.base_url}/{listing_id}"

            payload = {"access_token": self.access_token}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(url, params=payload)
                response.raise_for_status()

            logger.info(f"Item deleted from Facebook: {listing_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete item: {e}")
            return False
```

**Checklist:**
- [ ] Create `backend/app/market/facebook_client.py`
- [ ] Implement post_item() method
- [ ] Implement _upload_photo() method
- [ ] Implement update_item() method
- [ ] Implement delete_item() method
- [ ] Add error handling and logging

---

#### Task 1.3: Extend POST /seller/post for Facebook
**File:** `backend/app/seller/post.py` (MODIFY)
**Time:** 1-2 hours

```python
# Add to existing post.py:

async def post_to_facebook(
    item_id: int,
    marketplace_account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Post item to Facebook Marketplace."""

    # Get item
    item = db.query(MyItem).filter(MyItem.id == item_id).first()
    if not item:
        raise NotFoundError("MyItem", item_id)

    # Get marketplace account
    account = db.query(MarketplaceAccount).filter(
        MarketplaceAccount.id == marketplace_account_id,
        MarketplaceAccount.user_id == current_user.id,
        MarketplaceAccount.marketplace == "facebook"
    ).first()

    if not account:
        raise NotFoundError("MarketplaceAccount", marketplace_account_id)

    # Create Facebook client
    fb_client = FacebookMarketplaceClient(
        access_token=account.access_token,
        page_id=account.marketplace_account_id
    )

    # Get item images
    images = [photo.url for photo in item.photos]

    # Post to Facebook
    listing_id = await fb_client.post_item(
        title=item.title,
        description=item.description,
        price=item.price,
        images=images,
        category=map_category_to_facebook(item.category),
        condition=item.condition.value.upper() if item.condition else "USED",
    )

    if not listing_id:
        raise HTTPException(
            status_code=500,
            detail="Failed to post to Facebook Marketplace"
        )

    # Create cross-post record
    cross_post = CrossPost(
        item_id=item_id,
        marketplace="facebook",
        marketplace_listing_id=listing_id,
        status="published",
        posted_at=datetime.utcnow(),
    )
    db.add(cross_post)
    db.commit()

    return {
        "success": True,
        "marketplace": "facebook",
        "listing_id": listing_id,
        "url": f"https://www.facebook.com/marketplace/item/{listing_id}",
    }
```

**Checklist:**
- [ ] Add post_to_facebook() function
- [ ] Add category mapping function
- [ ] Update main POST /seller/post to support Facebook
- [ ] Test with sample items

---

### Day 2: Offerup Integration (Dev 1 or Dev 2)

#### Task 2.1: Create Offerup OAuth Route
**File:** `backend/app/routes/offerup_oauth.py`
**Lines:** ~120
**Time:** 1.5-2 hours

Similar to Facebook but simpler OAuth flow. Offerup uses standard OAuth 2.0.

```python
"""Offerup OAuth flow."""

from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx
from app.core.auth import get_current_user
from app.core.db import SessionLocal
from app.core.models import User, MarketplaceAccount
from app.config import get_settings

router = APIRouter(prefix="/offerup", tags=["offerup-oauth"])

@router.get("/authorize")
async def offerup_authorize(current_user: User = Depends(get_current_user)):
    """Generate Offerup OAuth authorization URL."""
    settings = get_settings()

    auth_url = "https://accounts.offerup.com/oauth/authorize"
    params = {
        "client_id": settings.offerup_client_id,
        "redirect_uri": f"{settings.backend_url}/offerup/callback",
        "response_type": "code",
        "scope": "listings:write listings:read",
    }

    url = f"{auth_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"

    return {"authorization_url": url}


@router.get("/callback")
async def offerup_callback(
    code: str = Query(...),
    db: Session = Depends(get_db),
):
    """Handle OAuth callback and store credentials."""
    settings = get_settings()

    # Exchange code for token
    token_url = "https://accounts.offerup.com/oauth/token"

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.offerup_client_id,
        "client_secret": settings.offerup_client_secret,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, json=payload)
        response.raise_for_status()
        token_data = response.json()

    access_token = token_data["access_token"]

    # Store in database
    # Similar to Facebook but simpler
    # ...

    return {"success": True}
```

**Checklist:**
- [ ] Create `backend/app/routes/offerup_oauth.py`
- [ ] Implement authorize endpoint
- [ ] Implement callback handler
- [ ] Store access token in database

---

#### Task 2.2: Create Offerup Client
**File:** `backend/app/market/offerup_client.py`
**Lines:** ~180
**Time:** 1.5-2 hours

```python
"""Offerup API client."""

import httpx
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class OfferupClient:
    """Client for Offerup API."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.offerup.com/v1"

    async def post_item(
        self,
        title: str,
        description: str,
        price: float,
        images: List[str],
        category: str,
        location: Dict[str, float],  # {"latitude": x, "longitude": y}
        condition: str = "used",
    ) -> Optional[str]:
        """
        Post item to Offerup.

        Args:
            title: Item title
            description: Item description
            price: Price in dollars
            images: List of image URLs
            category: Offerup category
            location: GPS coordinates
            condition: Item condition

        Returns:
            Offerup listing ID
        """
        try:
            url = f"{self.base_url}/listings"

            payload = {
                "title": title,
                "description": description,
                "price_cents": int(price * 100),
                "photos": images,
                "category": category,
                "location": location,
                "condition": condition,
            }

            headers = {"Authorization": f"Bearer {self.access_token}"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()

            result = response.json()
            listing_id = result.get("id")

            logger.info(f"Item posted to Offerup: {listing_id}")
            return listing_id

        except Exception as e:
            logger.error(f"Failed to post to Offerup: {e}")
            return None

    async def update_item(
        self,
        listing_id: str,
        **kwargs
    ) -> bool:
        """Update item on Offerup."""
        try:
            url = f"{self.base_url}/listings/{listing_id}"

            headers = {"Authorization": f"Bearer {self.access_token}"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    url,
                    json=kwargs,
                    headers=headers
                )
                response.raise_for_status()

            return True

        except Exception as e:
            logger.error(f"Failed to update Offerup listing: {e}")
            return False

    async def delete_item(self, listing_id: str) -> bool:
        """Delete item from Offerup."""
        try:
            url = f"{self.base_url}/listings/{listing_id}"

            headers = {"Authorization": f"Bearer {self.access_token}"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(url, headers=headers)
                response.raise_for_status()

            return True

        except Exception as e:
            logger.error(f"Failed to delete Offerup listing: {e}")
            return False
```

**Checklist:**
- [ ] Create `backend/app/market/offerup_client.py`
- [ ] Implement post_item() with location awareness
- [ ] Implement update_item()
- [ ] Implement delete_item()
- [ ] Add error handling

---

### Day 3: Integration & Testing

#### Task 3.1: Extend POST /seller/post for Offerup
**File:** `backend/app/seller/post.py` (MODIFY)
**Time:** 1 hour

Add similar function to post_to_facebook() but for Offerup with location support.

**Checklist:**
- [ ] Add post_to_offerup() function
- [ ] Add location mapping
- [ ] Update POST /seller/post endpoint
- [ ] Test with multiple items

---

#### Task 3.2: Update Database Models
**File:** `backend/app/core/models.py` (MODIFY)
**Time:** 1 hour

```python
# Add to MarketplaceAccount:
facebook_page_id: Optional[str]
facebook_business_account_id: Optional[str]
offerup_user_id: Optional[str]

# Add to CrossPost:
posted_at: datetime
last_updated_at: datetime
marketplace_url: Optional[str]  # Direct link to listing
```

**Checklist:**
- [ ] Add fields to MarketplaceAccount
- [ ] Add fields to CrossPost
- [ ] Create database migration

---

#### Task 3.3: Create Integration Tests
**File:** `backend/tests/test_facebook_offerup_integration.py`
**Time:** 2-3 hours

```python
"""Tests for marketplace integrations."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_facebook_oauth_flow(client: AsyncClient, test_user):
    """Test Facebook OAuth authorization flow."""

    response = await client.get(
        "/facebook/authorize",
        headers={"Authorization": f"Bearer {test_user.token}"}
    )

    assert response.status_code == 200
    assert "authorization_url" in response.json()


@pytest.mark.asyncio
async def test_post_item_to_facebook(client: AsyncClient, test_user, test_item):
    """Test posting item to Facebook."""

    response = await client.post(
        "/seller/post",
        json={
            "item_id": test_item.id,
            "marketplaces": ["facebook"],
            "marketplace_account_id": test_user.facebook_account.id,
        },
        headers={"Authorization": f"Bearer {test_user.token}"}
    )

    assert response.status_code == 200
    assert response.json()["success"] == True
    assert "listing_id" in response.json()


@pytest.mark.asyncio
async def test_post_item_to_offerup(client: AsyncClient, test_user, test_item):
    """Test posting item to Offerup."""

    response = await client.post(
        "/seller/post",
        json={
            "item_id": test_item.id,
            "marketplaces": ["offerup"],
            "marketplace_account_id": test_user.offerup_account.id,
        },
        headers={"Authorization": f"Bearer {test_user.token}"}
    )

    assert response.status_code == 200
    assert response.json()["success"] == True


@pytest.mark.asyncio
async def test_post_to_multiple_marketplaces(client: AsyncClient, test_user, test_item):
    """Test posting same item to multiple marketplaces."""

    response = await client.post(
        "/seller/post",
        json={
            "item_id": test_item.id,
            "marketplaces": ["facebook", "offerup", "ebay"],
        },
        headers={"Authorization": f"Bearer {test_user.token}"}
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 3
    assert all(r["success"] for r in results)
```

**Checklist:**
- [ ] Create test file
- [ ] Write OAuth flow tests
- [ ] Write item posting tests
- [ ] Write multi-marketplace tests
- [ ] Run and verify all tests pass

---

#### Task 3.4: Update Configuration
**File:** `backend/app/config.py` (MODIFY)
**Time:** 30 minutes

```python
# Add to Settings class:
facebook_app_id: str = env.get("FACEBOOK_APP_ID")
facebook_app_secret: str = env.get("FACEBOOK_APP_SECRET")

offerup_client_id: str = env.get("OFFERUP_CLIENT_ID")
offerup_client_secret: str = env.get("OFFERUP_CLIENT_SECRET")

# Also update .env template
```

**Checklist:**
- [ ] Add Facebook config
- [ ] Add Offerup config
- [ ] Update environment template
- [ ] Add to Docker environment variables

---

#### Task 3.5: Create Documentation
**File:** `MARKETPLACE_SETUP_GUIDE.md` (NEW)
**Time:** 1-2 hours

```markdown
# Marketplace Integration Setup Guide

## Facebook Marketplace

### Prerequisites
1. Create Facebook App at developers.facebook.com
2. Add "Marketplace" product
3. Get App ID and App Secret
4. Set redirect URI: https://your-domain.com/facebook/callback

### Configuration
```
FACEBOOK_APP_ID=xxx
FACEBOOK_APP_SECRET=yyy
```

### Usage
1. User clicks "Connect Facebook"
2. Redirected to Facebook login
3. Grants permission to app
4. App stores access token
5. User can now post items

## Offerup Integration

...
```

**Checklist:**
- [ ] Create setup guide
- [ ] Document API usage
- [ ] Add troubleshooting section
- [ ] Add seller walkthrough

---

### Day 4-5: Testing & Deployment

#### Task 4.1: Integration Testing
**File:** Various test files
**Time:** 2-3 hours

```
✓ Test Facebook OAuth flow with sandbox
✓ Test Offerup OAuth flow
✓ Test item posting (with mock data)
✓ Test error handling (expired tokens)
✓ Test image upload
✓ Test category mapping
✓ Test webhook handling
```

**Checklist:**
- [ ] Test all OAuth flows
- [ ] Test item posting
- [ ] Test error scenarios
- [ ] Verify logs are clean
- [ ] Load test (100+ concurrent posts)

---

#### Task 4.2: Staging Deployment
**File:** Docker compose / deployment scripts
**Time:** 1 hour

```bash
# Deploy to staging
git checkout -b feature/marketplace-integrations
git push origin feature/marketplace-integrations

# Create pull request
# Code review
# Merge to master
# Deploy to staging.domain.com
```

**Checklist:**
- [ ] Create feature branch
- [ ] Push code
- [ ] Create pull request
- [ ] Code review
- [ ] Merge to master
- [ ] Deploy to staging

---

#### Task 4.3: User Documentation
**File:** User docs
**Time:** 1 hour

- How to connect marketplaces
- How to post items
- Troubleshooting guide
- FAQ

**Checklist:**
- [ ] Create seller documentation
- [ ] Create API documentation
- [ ] Add to README
- [ ] Add to wiki

---

#### Task 4.4: Production Deployment
**File:** Production configuration
**Time:** 1-2 hours

```bash
# When ready for production:
git tag v6.1-marketplace-integrations
git push origin --tags

# Deploy to production with:
- Feature flags (optional rollout)
- Monitoring alerts
- Rollback plan ready
```

**Checklist:**
- [ ] Enable monitoring
- [ ] Set up alerts
- [ ] Prepare rollback
- [ ] Gradual rollout (10% → 50% → 100%)
- [ ] Monitor error rates
- [ ] Track success metrics

---

## Sprint 1 Checklist Summary

### Code Completion:
- [ ] Facebook OAuth route (`facebook_oauth.py`)
- [ ] Facebook API client (`facebook_client.py`)
- [ ] Offerup OAuth route (`offerup_oauth.py`)
- [ ] Offerup API client (`offerup_client.py`)
- [ ] POST /seller/post integration
- [ ] Database migrations
- [ ] Configuration updates

### Testing:
- [ ] Unit tests for all functions
- [ ] Integration tests for OAuth flows
- [ ] Integration tests for item posting
- [ ] Error handling tests
- [ ] Load testing

### Documentation:
- [ ] API documentation
- [ ] Marketplace setup guide
- [ ] Seller walkthrough
- [ ] Troubleshooting guide

### Deployment:
- [ ] Code review
- [ ] Staging deployment
- [ ] Production deployment
- [ ] Monitoring setup
- [ ] Rollback ready

---

## Success Metrics

After Sprint 1 completion, measure:

✅ **Functionality:**
- Facebook and Offerup OAuth working
- Items posting successfully
- Cross-post records created
- Webhooks received

✅ **User Adoption:**
- 50%+ of sellers connected
- 1,000+ items cross-posted
- 0 errors in first week

✅ **Performance:**
- Item posting: <2 seconds
- API response time: <500ms
- Error rate: <0.1%

✅ **Business:**
- 3-4x seller reach expansion
- Revenue increase from more marketplace fees

---

## Transition to Sprint 2

After Sprint 1 completes, move to **Sprint 2: Deal Alert Rules & Notifications**

Next sprint deliverables:
- Custom deal alert rules
- Multi-channel notifications
- Digest email system
- Background task automation

---

**Sprint 1 Ready? Let's build! 🚀**

---

Generated: October 29, 2025
Status: Ready for Implementation
