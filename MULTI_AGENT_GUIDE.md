# Multi-Agent Concurrent Processing Guide

Deal Scout is optimized for handling multiple concurrent photo processing requests using Celery's multi-agent architecture.

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│                  MULTI-AGENT PROCESSING                    │
└────────────────────────────────────────────────────────────┘

Frontend Upload → Redis Queue → Multiple Celery Workers → Gemini API

User 1 → Photo A ──┐
User 2 → Photo B ──┼──→ Redis ──→ Worker 1 (4 threads) ──→ Gemini
User 3 → Photo C ──┤           ├→ Worker 2 (4 threads) ──→ Gemini
User 4 → Photo D ──┘           ├→ Worker 3 (4 threads) ──→ Gemini
                               └→ Worker N (4 threads) ──→ Gemini
```

## Celery Configuration

### Current Settings (Optimized for Concurrency)

```python
# backend/app/worker.py
celery_app.conf.update(
    worker_prefetch_multiplier=4,      # Prefetch 4 tasks per worker
    worker_max_tasks_per_child=100,    # Restart after 100 tasks
    task_acks_late=True,                # Acknowledge after completion
    task_reject_on_worker_lost=True,    # Re-queue if worker dies
    worker_pool='prefork',              # Prefork for CPU-bound tasks
    worker_concurrency=4,               # 4 concurrent tasks per worker
    task_compression='gzip',            # Compress messages
    task_time_limit=300,                # 5 minute hard limit
    task_soft_time_limit=240,           # 4 minute soft limit
)
```

## Scaling Strategies

### Local Development (Single Machine)

**Start a single worker with 4 concurrent processes:**
```bash
celery -A app.worker worker --loglevel=info --concurrency=4
```

**Start multiple workers (for testing multi-agent):**
```bash
# Terminal 1
celery -A app.worker worker --loglevel=info --concurrency=4 -n worker1@%h

# Terminal 2
celery -A app.worker worker --loglevel=info --concurrency=4 -n worker2@%h

# Terminal 3
celery -A app.worker worker --loglevel=info --concurrency=4 -n worker3@%h
```

This gives you **12 concurrent agents** (3 workers × 4 concurrency).

### Production (Multi-Machine)

#### Render Deployment (Recommended)

**Option 1: Single Worker Service (4 concurrent agents)**
```yaml
# render.yaml
- type: worker
  name: deal-scout-worker
  env: python
  buildCommand: pip install -e .
  startCommand: celery -A app.worker worker --loglevel=info --concurrency=4
```

**Option 2: Multiple Worker Services (12+ concurrent agents)**
```yaml
# render.yaml
- type: worker
  name: deal-scout-worker-1
  env: python
  buildCommand: pip install -e .
  startCommand: celery -A app.worker worker --loglevel=info --concurrency=4 -n worker1@%h

- type: worker
  name: deal-scout-worker-2
  env: python
  buildCommand: pip install -e .
  startCommand: celery -A app.worker worker --loglevel=info --concurrency=4 -n worker2@%h

- type: worker
  name: deal-scout-worker-3
  env: python
  buildCommand: pip install -e .
  startCommand: celery -A app.worker worker --loglevel=info --concurrency=4 -n worker3@%h
```

Each additional worker service costs **$7/month** on Render Starter plan.

#### Docker Compose (Development/Testing)

```yaml
# docker-compose.yml
services:
  worker-1:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info --concurrency=4 -n worker1@%h
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}

  worker-2:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info --concurrency=4 -n worker2@%h
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}

  worker-3:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info --concurrency=4 -n worker3@%h
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
```

## Performance Tuning

### Concurrency Settings

| Workers | Concurrency | Total Agents | Use Case |
|---------|-------------|--------------|----------|
| 1       | 2           | 2            | Minimal (Free tier) |
| 1       | 4           | 4            | Development |
| 2       | 4           | 8            | Small production |
| 3       | 4           | 12           | Medium production |
| 4       | 8           | 32           | High volume |

### Adjusting Concurrency

**Command-line override:**
```bash
# Start worker with 8 concurrent agents
celery -A app.worker worker --loglevel=info --concurrency=8
```

**Environment variable:**
```bash
export CELERYD_CONCURRENCY=8
celery -A app.worker worker --loglevel=info
```

### Prefetch Multiplier

Controls how many tasks a worker grabs ahead of time:

```python
# Aggressive prefetching (better throughput)
worker_prefetch_multiplier=4  # Each worker prefetches 4 × concurrency tasks

# Conservative prefetching (better distribution)
worker_prefetch_multiplier=1  # Each worker only prefetches 1 task at a time
```

**Rule of thumb:**
- **High prefetch (4)**: Use when all workers are equally fast
- **Low prefetch (1)**: Use when workers have varying speeds

## Monitoring & Observability

### Check Active Workers

```bash
celery -A app.worker inspect active
```

Output:
```json
{
  "worker1@hostname": [...],
  "worker2@hostname": [...],
  "worker3@hostname": [...]
}
```

### Monitor Queue Depth

```bash
celery -A app.worker inspect reserved
```

### Check Worker Stats

```bash
celery -A app.worker inspect stats
```

### Flower Dashboard (Optional)

**Install:**
```bash
pip install flower
```

**Run:**
```bash
celery -A app.worker flower --port=5555
```

**Access:** http://localhost:5555

Shows:
- Active workers
- Queue lengths
- Task success/failure rates
- Real-time monitoring

## Google Gemini API Limits

### Rate Limits (Gemini 1.5 Pro)

| Tier | Requests/Minute | Requests/Day |
|------|-----------------|--------------|
| Free | 2 RPM           | 50 RPD       |
| Pay-as-you-go | 1000 RPM | Unlimited |

### Handling Rate Limits

**Celery Retry Configuration:**

```python
# backend/app/tasks/process_snap.py
@shared_task(
    name="app.tasks.process_snap.process_snap_job",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minute backoff
    retry_jitter=True,
    max_retries=3,
)
def process_snap_job(job_id: int):
    # Task implementation
    ...
```

**Rate Limiting Queue:**

```python
# backend/app/worker.py
celery_app.conf.task_routes = {
    'app.tasks.process_snap.process_snap_job': {
        'queue': 'gemini',
        'rate_limit': '50/m',  # 50 requests per minute
    },
}
```

Then start a dedicated worker for Gemini tasks:
```bash
celery -A app.worker worker -Q gemini --loglevel=info --concurrency=2
```

## Load Testing

### Simulate Concurrent Uploads

```python
# scripts/load_test_concurrent.py
import asyncio
import httpx

async def upload_photo(client, image_path):
    with open(image_path, 'rb') as f:
        image_data = f.read()

    response = await client.post(
        'http://localhost:8000/seller/snap',
        json={'photos': [base64.b64encode(image_data).decode()]}
    )
    return response.json()

async def main():
    async with httpx.AsyncClient() as client:
        # Simulate 50 concurrent uploads
        tasks = [
            upload_photo(client, f'test_images/photo_{i}.jpg')
            for i in range(50)
        ]
        results = await asyncio.gather(*tasks)
        print(f"Completed {len(results)} uploads")

if __name__ == '__main__':
    asyncio.run(main())
```

### Metrics to Track

- **Queue depth**: Should remain low under normal load
- **Task processing time**: Should be consistent (30-60s per photo)
- **Error rate**: Should be <1% (excluding API rate limits)
- **Worker utilization**: Should be 70-90% (higher = good throughput)

## Cost Optimization

### Gemini API Pricing

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|----------------------|
| Gemini 1.5 Pro | $1.25 | $5.00 |
| Gemini 1.5 Flash | $0.075 | $0.30 |

**Estimated costs per photo:**
- **Gemini 1.5 Pro**: ~$0.02-0.05 per photo (vision + pricing)
- **Gemini 1.5 Flash**: ~$0.001-0.003 per photo (text-only tasks)

**Strategy:**
- Use **Gemini 1.5 Pro** for vision (item detection)
- Use **Gemini 1.5 Flash** for pricing estimation (faster + cheaper)

### Worker Costs (Render)

| Configuration | Monthly Cost |
|---------------|-------------|
| 1 worker (4 concurrency) | $7 |
| 2 workers (8 total agents) | $14 |
| 3 workers (12 total agents) | $21 |
| 4 workers (16 total agents) | $28 |

**Break-even analysis:**
- At 500 photos/month: 1 worker sufficient
- At 2000 photos/month: 2-3 workers recommended
- At 10000+ photos/month: 4+ workers + horizontal scaling

## Troubleshooting

### Workers Not Processing Tasks

**Check worker status:**
```bash
celery -A app.worker inspect active
```

**Check queue:**
```bash
redis-cli
> LLEN celery  # Should show pending task count
```

**Restart workers:**
```bash
docker-compose restart worker
# or
supervisorctl restart celery-worker
```

### High Queue Depth

**Symptoms:** Queue depth grows faster than processing rate

**Solutions:**
1. Add more workers
2. Increase concurrency per worker
3. Check for slow tasks (timeout issues)
4. Verify Gemini API key is valid

### Memory Issues

**Symptoms:** Workers crash or restart frequently

**Solutions:**
1. Reduce `worker_max_tasks_per_child` (current: 100)
2. Reduce `worker_concurrency` (current: 4)
3. Add more RAM to worker machines
4. Use `worker_pool='gevent'` for I/O-bound tasks

### Rate Limit Errors

**Symptoms:** Tasks failing with "429 Too Many Requests"

**Solutions:**
1. Implement rate limiting (see "Rate Limiting Queue" above)
2. Upgrade Gemini API tier
3. Add retry logic with exponential backoff
4. Use task queues with throttling

## Best Practices

1. **Monitor Queue Depth**: Keep it < 10× worker count
2. **Use Flower**: Real-time dashboard is invaluable
3. **Set Task Timeouts**: Prevent zombie tasks
4. **Enable Compression**: Reduces Redis memory
5. **Log Everything**: Structured logging for debugging
6. **Graceful Shutdown**: Use `SIGTERM` not `SIGKILL`
7. **Auto-restart**: Use `worker_max_tasks_per_child` to prevent memory leaks
8. **Horizontal Scaling**: Add workers before increasing concurrency

## Example Deployment Commands

### Development
```bash
# Start 2 workers locally
celery -A app.worker worker --loglevel=info --concurrency=4 -n worker1@%h &
celery -A app.worker worker --loglevel=info --concurrency=4 -n worker2@%h &
celery -A app.worker beat --loglevel=info &
```

### Production (systemd)
```ini
# /etc/systemd/system/celery-worker@.service
[Unit]
Description=Celery Worker %i
After=network.target redis.service postgresql.service

[Service]
Type=forking
User=celery
Group=celery
WorkingDirectory=/app/backend
ExecStart=/usr/local/bin/celery -A app.worker worker \
    --loglevel=info \
    --concurrency=4 \
    -n worker%i@%%h \
    --pidfile=/var/run/celery/worker%i.pid \
    --logfile=/var/log/celery/worker%i.log
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable multiple workers:
```bash
systemctl enable celery-worker@1
systemctl enable celery-worker@2
systemctl enable celery-worker@3
systemctl start celery-worker@{1,2,3}
```

---

**Result:** A scalable, multi-agent concurrent processing system that can handle hundreds of photo uploads per minute! 🚀
