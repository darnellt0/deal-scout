# Copywriter Feature Documentation

## Overview

The copywriter feature provides AI-powered text generation for marketplace listings, generating comprehensive copy including titles, descriptions, bullet point highlights, and tags to optimize listing performance.

## Architecture

### Components

1. **`app/seller/copywriter.py`** - Core copywriter module
   - `generate_copy()` - Main function for generating comprehensive listing copy
   - Fallback functions for when OpenAI is unavailable
   - Legacy `generate_listing()` for backwards compatibility

2. **`app/tasks/copywriter.py`** - Celery task wrapper
   - `write_listing()` - Celery task for async copywriter execution
   - Reads from SnapJob, generates copy, stores results

3. **`app/tasks/process_snap.py`** - Pipeline integration
   - Calls copywriter as part of the snap processing pipeline
   - Stores results in SnapJob model

## Data Flow

```
SnapJob (input)
  ├─ detected_category
  ├─ detected_attributes
  ├─ condition_guess
  ├─ suggested_price
  └─ processed_images
         ↓
    generate_copy()
         ↓
SnapJob (output)
  ├─ suggested_title
  ├─ suggested_description
  ├─ title_suggestion
  ├─ description_suggestion
  └─ meta.copy
       ├─ title
       ├─ description
       ├─ highlights (list)
       ├─ tags (list)
       └─ confidence (float)
```

## Database Schema

### SnapJob Model Changes

A new `metadata` JSON column has been added to store structured copywriter data:

```python
class SnapJob(Base):
    # ... existing fields ...
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
```

### Meta.copy Structure

```json
{
  "copy": {
    "title": "Dell XPS 13 Laptop - Excellent Condition",
    "description": "High-performance Dell XPS 13...",
    "highlights": [
      "Dell XPS 13 model",
      "Excellent condition",
      "Fast Intel processor",
      "Long battery life",
      "Includes original charger"
    ],
    "tags": [
      "laptop",
      "dell",
      "xps",
      "computer",
      "ultrabook",
      "portable",
      "business",
      "student"
    ],
    "confidence": 0.9
  }
}
```

## API Usage

### Generate Copy (Function)

```python
from app.seller.copywriter import generate_copy

copy_data = generate_copy(
    category="laptop",
    attributes={"brand": "Dell", "model": "XPS 13", "color": "Silver"},
    condition="excellent",
    price=500.0,
    photos_count=3
)

# Returns:
# {
#   "title": "...",
#   "description": "...",
#   "highlights": [...],
#   "tags": [...],
#   "confidence": 0.9
# }
```

### Celery Task Usage

```python
from app.tasks.copywriter import write_listing

# Async execution
result = write_listing.delay(job_id=123)

# Sync execution (for testing)
result = write_listing(job_id=123)
```

### Pipeline Integration

The copywriter is automatically called as part of the `process_snap_job` pipeline:

```python
# In process_snap.py
copy_data = generate_copy(
    category=category,
    attributes=attributes,
    condition=condition,
    price=suggested_price,
    photos_count=photos_count,
)

# Results stored in SnapJob
job.suggested_title = copy_data["title"]
job.suggested_description = copy_data["description"]
job.meta["copy"] = copy_data
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - OpenAI API key for GPT-4o-mini (optional)
  - If not set, falls back to template-based copy generation

### OpenAI Integration

When configured, the copywriter uses OpenAI's GPT-4o-mini model:

```python
model = "gpt-4o-mini"
temperature = 0.7
max_tokens = 1000
```

The prompt instructs the model to:
- Create keyword-rich titles under 80 characters
- Write 2-4 paragraph descriptions with details and benefits
- Generate 3-5 key features as bullet points
- Suggest 5-10 relevant search tags
- Return results as JSON

## Fallback Behavior

When OpenAI is unavailable (no API key or error), the system uses intelligent fallbacks:

### Fallback Title
```
{brand} {model} {category} - {color}
Example: "Dell XPS 13 Laptop - Silver"
```

### Fallback Description
```
Quality {category} in {condition} condition.

Item Details:
- Brand: {brand}
- Model: {model}
- Color: {color}
- Size: {size}

Sourced and verified via Deal Scout.
Competitively priced at ${price}.

Please review photos and contact with any questions.
```

### Fallback Highlights
- Condition: {condition}
- Brand: {brand}
- Model: {model}
- Color: {color}
- Size: {size}

### Fallback Tags
- {category}
- {brand}
- {model}
- {color}
- {material}
- quality
- deal
- resale

## Database Migration

To add the `metadata` field to existing databases:

```bash
cd backend
alembic upgrade head
```

Migration file: `backend/alembic/versions/add_meta_field_to_snapjob.py`

## Testing

### Run Unit Tests

```bash
cd backend
pytest tests/test_copywriter.py -v
```

### Test Coverage

The test suite covers:
- Generate copy without OpenAI (fallback mode)
- Generate copy with OpenAI success
- Generate copy with OpenAI error (fallback)
- Title length limits (80 chars)
- Highlights limits (5 items)
- Tags limits (10 items)
- All fallback helper functions

### Manual Testing

```python
# In Python shell
from app.seller.copywriter import generate_copy

result = generate_copy(
    category="couch",
    attributes={"color": "gray", "material": "fabric"},
    condition="good",
    price=200.0,
    photos_count=4
)

print(result)
```

## Performance Considerations

### OpenAI API Calls
- Each call takes ~1-3 seconds
- Included in the synchronous snap processing pipeline
- Fallback is immediate (no external API call)

### Caching
- Currently no caching implemented
- Future enhancement: cache results by (category, attributes, condition) hash

### Rate Limiting
- OpenAI has rate limits (check your plan)
- Consider implementing retry logic for transient errors
- Consider batching if processing many items

## Future Enhancements

1. **Multi-marketplace Optimization**
   - Generate marketplace-specific copy (eBay, Facebook, Craigslist)
   - Adapt tone and format per platform

2. **A/B Testing**
   - Generate multiple variants
   - Track performance metrics
   - Learn from successful listings

3. **Keyword Optimization**
   - SEO keyword analysis
   - Trending search terms integration
   - Competitive keyword research

4. **Localization**
   - Multi-language support
   - Region-specific terminology
   - Cultural adaptation

5. **Enhanced Context**
   - Use actual image analysis (not just metadata)
   - Incorporate pricing context
   - Reference comp listings for style matching

6. **Quality Scoring**
   - Validate generated copy quality
   - Check for completeness
   - Flag potential issues

## Error Handling

The copywriter is designed to never fail completely:

1. **OpenAI unavailable** → Use fallback templates
2. **Invalid JSON response** → Parse what's possible, use fallback for rest
3. **API error** → Log warning, use fallback
4. **Missing input data** → Use sensible defaults

All errors are logged but don't block the snap processing pipeline.

## API Endpoints

### Get SnapJob with Copy Data

```bash
GET /seller/snap/{job_id}
```

Response includes full copy data in `meta.copy`:

```json
{
  "id": 123,
  "status": "ready",
  "detected_category": "laptop",
  "detected_attributes": {"brand": "Dell", "model": "XPS 13"},
  "condition_guess": "good",
  "suggested_price": 500.0,
  "suggested_title": "Dell XPS 13 Laptop",
  "suggested_description": "High quality Dell XPS 13...",
  "meta": {
    "copy": {
      "title": "Dell XPS 13 Laptop",
      "description": "High quality Dell XPS 13...",
      "highlights": ["..."],
      "tags": ["..."],
      "confidence": 0.9
    }
  }
}
```

## Troubleshooting

### Copy Not Generated

**Check:**
1. OpenAI API key configured correctly in `.env`
2. SnapJob has detected_category and detected_attributes
3. Celery worker is running
4. Check logs for errors: `docker logs deal-scout-worker`

### Low Quality Copy

**Check:**
1. Input data quality (category, attributes, condition)
2. OpenAI API key is valid and working
3. Fallback mode is being used (check confidence score)
4. Review logs for API errors

### OpenAI Timeout

**Adjust:**
1. Increase timeout in copywriter.py
2. Switch to fallback mode temporarily
3. Check OpenAI service status

## Code Examples

### Access Copy Data in Frontend

```typescript
// In React/Next.js component
const snapJob = await fetch(`/api/seller/snap/${jobId}`).then(r => r.json())

const title = snapJob.meta?.copy?.title || snapJob.suggested_title
const description = snapJob.meta?.copy?.description
const highlights = snapJob.meta?.copy?.highlights || []
const tags = snapJob.meta?.copy?.tags || []

// Display highlights
<ul>
  {highlights.map((highlight, i) => (
    <li key={i}>{highlight}</li>
  ))}
</ul>

// Display tags
<div className="tags">
  {tags.map((tag, i) => (
    <span key={i} className="tag">{tag}</span>
  ))}
</div>
```

### Custom Copy Generation

```python
from app.seller.copywriter import generate_copy

# Override for specific marketplace
copy = generate_copy(
    category="furniture",
    attributes={"type": "couch", "seats": "3", "color": "blue"},
    condition="excellent",
    price=300.0
)

# Customize for platform
if platform == "ebay":
    title = copy["title"][:80]  # eBay limit
elif platform == "facebook":
    title = copy["title"]  # No specific limit
```

## Support

For issues or questions:
1. Check logs: `docker logs deal-scout-worker`
2. Review test cases: `tests/test_copywriter.py`
3. See main documentation: `README.md`
