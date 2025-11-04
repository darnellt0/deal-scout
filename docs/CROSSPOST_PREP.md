# Cross-Post Prep Feature

## Overview

The Cross-Post Prep feature (step 2.6 in the snap processing pipeline) automatically prepares marketplace-specific metadata for your items, making it easy to cross-post to multiple marketplaces like eBay, Facebook Marketplace, and OfferUp.

## Architecture

### Pipeline Flow

When a snap job is processed with cross-post prep enabled, the following happens:

```
1. Vision → Detect item
2. Image Prep → Clean/standardize
3. Pricing → Pull comps & suggest price
4. Copywriter → Draft listing text
5. Compose Draft → Save MyItem
6. **Cross-post prep** → Generate marketplace metadata (NEW!)
7. Finalize Job
```

### Key Components

#### 1. Celery Tasks (`app/tasks/cross_post.py`)

- **`prepare_crosspost(job_id, platforms)`**
  - Generates marketplace-specific metadata
  - Creates `CrossPost` records with `status="pending"`
  - Called automatically if `enable_crosspost_prep=True`

- **`post_to_marketplaces(item_id, platforms)`**
  - Actually posts items to marketplaces
  - Processes all pending `CrossPost` records
  - Updates status to `"live"` or `"failed"`

#### 2. API Endpoints

##### Create Snap with Cross-Post Prep

```http
POST /api/proxy/seller/snap
Content-Type: application/json

{
  "photos": ["https://example.com/photo1.jpg"],
  "enable_crosspost_prep": true,
  "crosspost_platforms": ["ebay", "facebook", "offerup"]
}
```

**Response:**
```json
{
  "job_id": 123,
  "status": "queued"
}
```

##### Publish to Marketplaces

After the snap job completes, you can trigger actual posting:

```http
POST /api/proxy/seller/publish/{item_id}
```

This will process all pending cross-posts for that item.

## Marketplace-Specific Metadata

### eBay

Generated metadata includes:
- SKU: `DEALSCOUT-{item_id}`
- Category ID (mapped from internal category)
- Item Specifics (Brand, Model, Color, Size, Condition)
- Listing policies (shipping, return, payment)

**Category Mapping:**
- `electronics` → eBay category 293
- `clothing` → eBay category 11450
- `furniture` → eBay category 3197
- `books` → eBay category 267

### Facebook Marketplace

Generated metadata includes:
- Availability: `in_stock`
- Visibility: `PUBLIC`
- Category (mapped from internal category)
- Condition
- Custom label for tracking

**Category Mapping:**
- `electronics` → `electronics`
- `clothing` → `apparel`
- `furniture` → `furniture`
- `books` → `entertainment`

### OfferUp

Generated metadata includes:
- Location (latitude/longitude from user profile)
- Category (mapped from internal category)
- Condition
- Shipping settings (local pickup by default)

**Category Mapping:**
- `electronics` → `electronics`
- `clothing` → `clothing_and_shoes`
- `furniture` → `home_and_garden`
- `books` → `books_movies_and_music`

## Database Schema

### CrossPost Model

```python
class CrossPost(Base):
    __tablename__ = "cross_posts"

    id: int
    my_item_id: int                    # Links to MyItem
    platform: str                      # "ebay", "facebook", "offerup"
    external_id: Optional[str]         # Platform's listing ID
    listing_url: str                   # Public listing URL
    status: str                        # "pending", "live", "failed", "closed"
    meta: dict                         # Platform-specific metadata
    created_at: datetime
```

### Status Flow

1. **pending**: Created by `prepare_crosspost`, waiting to be posted
2. **live**: Successfully posted to marketplace
3. **failed**: Posting failed (error in `meta`)
4. **closed**: Item sold or delisted

## Usage Examples

### Example 1: Enable Cross-Post Prep for All Platforms

```python
import requests

response = requests.post(
    "https://api.dealscout.app/api/proxy/seller/snap",
    json={
        "photos": ["https://example.com/shoe.jpg"],
        "enable_crosspost_prep": True,
        # Platforms defaults to ["ebay", "facebook", "offerup"]
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

job_id = response.json()["job_id"]
```

### Example 2: Prepare for Specific Platforms Only

```python
response = requests.post(
    "https://api.dealscout.app/api/proxy/seller/snap",
    json={
        "photos": ["https://example.com/couch.jpg"],
        "enable_crosspost_prep": True,
        "crosspost_platforms": ["facebook", "offerup"]  # Skip eBay
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### Example 3: Check Cross-Post Status

```python
# After snap job completes, check what cross-posts were created
response = requests.get(
    f"https://api.dealscout.app/api/proxy/seller/items/{item_id}",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

item = response.json()
cross_posts = item.get("cross_posts", [])

for cp in cross_posts:
    print(f"{cp['platform']}: {cp['status']}")
    if cp['status'] == 'pending':
        print(f"  Ready to publish with metadata: {cp['meta']}")
```

### Example 4: Trigger Publishing

```python
# Manually trigger publishing to marketplaces
from app.tasks.cross_post import post_to_marketplaces

# Via Celery task
result = post_to_marketplaces.delay(item_id=123)

# Or via API endpoint (to be implemented)
response = requests.post(
    f"https://api.dealscout.app/api/proxy/seller/publish/{item_id}",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

## Configuration

### Default Platforms

By default, cross-post prep creates records for:
- eBay
- Facebook Marketplace
- OfferUp

### Customizing Category Mappings

To add or modify category mappings, edit the mapping functions in `app/tasks/cross_post.py`:

```python
def _map_category_to_ebay(category: str) -> str:
    category_map = {
        "electronics": "293",
        # Add your custom mappings here
        "vintage_toys": "220",
    }
    return category_map.get(category.lower(), "1")
```

### User Location for OfferUp

OfferUp requires location data. The system uses:
1. User profile location (if available)
2. Default: San Jose, CA (37.3382, -121.8863)

Update user location in the user profile:

```python
user.profile = {
    "location": {
        "latitude": 34.0522,
        "longitude": -118.2437
    }
}
```

## Error Handling

### Common Errors

1. **"my_item_not_found"**
   - The snap job completed, but no MyItem was created
   - Check that the snap processing pipeline completed successfully

2. **"user_not_found"**
   - User ID from snap job doesn't exist
   - Verify user authentication

3. **"Facebook account not connected"**
   - User hasn't connected their Facebook Marketplace account
   - Guide user to `/settings/marketplace-accounts`

4. **"OfferUp account not connected"**
   - User hasn't connected their OfferUp account
   - Guide user to `/settings/marketplace-accounts`

### Debugging

Enable debug logging for cross-post tasks:

```python
import logging

logging.getLogger("app.tasks.cross_post").setLevel(logging.DEBUG)
```

Check Celery task status:

```bash
# Check task status
celery -A app.worker inspect active

# Check failed tasks
celery -A app.worker inspect failed
```

## Testing

### Manual Testing

1. Create a snap job with cross-post prep:
```bash
curl -X POST http://localhost:8080/api/proxy/seller/snap \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "photos": ["https://example.com/test.jpg"],
    "enable_crosspost_prep": true
  }'
```

2. Wait for processing to complete (check status endpoint)

3. Verify CrossPost records were created:
```sql
SELECT * FROM cross_posts WHERE status = 'pending';
```

### Automated Testing

See `/backend/tests/test_cross_post.py` for integration tests.

## Future Enhancements

Potential improvements:

1. **Async Publishing**
   - Convert `post_to_marketplaces` to fully async
   - Use `asyncio` for parallel posting to multiple platforms

2. **Retry Logic**
   - Automatic retry for failed posts
   - Exponential backoff

3. **Platform Templates**
   - Customizable templates for each marketplace
   - User-defined field mappings

4. **Scheduling**
   - Schedule posts for specific times
   - Staggered posting to avoid spam detection

5. **Analytics**
   - Track cross-post performance by platform
   - A/B testing for titles/descriptions

## Support

For issues or questions:
- File a bug report at `/issues`
- Check logs in Celery worker output
- Review the CrossPost records in the database
