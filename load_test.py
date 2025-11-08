"""
Load testing script for Deal Scout using Locust
Installation: pip install locust
Run: locust -f load_test.py --host http://localhost:8000
"""

# Guard: fail fast if Locust is not installed
try:
    from locust import HttpUser, task, between, events
except ImportError as e:
    raise SystemExit(
        "Locust is not installed. Install with: pip install locust\n"
        "Or run dedicated load tests separately from unit CI."
    ) from e

import random
import json
from datetime import datetime, timedelta


class DealScoutUser(HttpUser):
    """Simulated Deal Scout user performing typical operations."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Initialize user session."""
        self.listings = []
        self.snap_jobs = []

    # ========================================================================
    # BUYER WORKFLOW TASKS
    # ========================================================================

    @task(5)
    def health_check(self):
        """Health check (simulates monitoring)."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(3)
    def get_listings(self):
        """Get listings with various filters."""
        filters = [
            {"category": "couches", "price_max": 200},
            {"category": "kitchen island", "price_max": 300},
            {"radius_mi": 25},
            {"radius_mi": 50},
        ]
        filter_params = random.choice(filters)

        with self.client.get("/listings", params=filter_params, catch_response=True) as response:
            if response.status_code == 200:
                self.listings = response.json()
                response.success()
            else:
                response.failure(f"Get listings failed: {response.status_code}")

    @task(2)
    def get_deals(self):
        """Get buyer deals feed."""
        params = {
            "limit": random.choice([10, 20, 50]),
            "min_score": random.choice([50, 60, 70]),
        }

        with self.client.get("/buyer/deals", params=params, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get deals failed: {response.status_code}")

    @task(1)
    def view_listing(self):
        """View a specific listing."""
        if self.listings:
            listing_id = random.choice(self.listings).get("id")
            with self.client.get(
                f"/listings/{listing_id}", catch_response=True
            ) as response:
                if response.status_code in [200, 404]:
                    response.success()
                else:
                    response.failure(f"View listing failed: {response.status_code}")

    # ========================================================================
    # SELLER WORKFLOW TASKS
    # ========================================================================

    @task(2)
    def create_snap_job(self):
        """Create a Snap Studio job for photo upload."""
        payload = {
            "input_photos": [
                "https://example.com/photo1.jpg",
                "https://example.com/photo2.jpg",
            ],
            "source": "upload",
        }

        with self.client.post(
            "/seller/snap",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                try:
                    job = response.json()
                    self.snap_jobs.append(job.get("id"))
                    response.success()
                except:
                    response.failure("Invalid response format")
            else:
                response.failure(f"Create snap job failed: {response.status_code}")

    @task(2)
    def get_snap_job_status(self):
        """Check Snap job status."""
        if self.snap_jobs:
            job_id = random.choice(self.snap_jobs)
            with self.client.get(
                f"/seller/snap/{job_id}",
                catch_response=True,
            ) as response:
                if response.status_code in [200, 404]:
                    response.success()
                else:
                    response.failure(f"Get snap job failed: {response.status_code}")

    @task(1)
    def suggest_price(self):
        """Get price suggestion for an item."""
        payload = {
            "title": "Couch in Good Condition",
            "category": "furniture",
            "condition": "good",
            "detected_attributes": {
                "color": "brown",
                "material": "fabric",
                "size": "3-seater",
            },
        }

        with self.client.post(
            "/seller/pricing/suggest",
            json=payload,
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Price suggestion failed: {response.status_code}")

    # ========================================================================
    # API STRESS TESTING
    # ========================================================================

    @task(1)
    def metrics(self):
        """Fetch Prometheus metrics (monitoring endpoint)."""
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Metrics fetch failed: {response.status_code}")

    @task(1)
    def api_errors(self):
        """Intentionally trigger some errors to test error handling."""
        # Invalid endpoint
        with self.client.get("/api/invalid", catch_response=True) as response:
            if response.status_code in [404, 405]:
                response.success()  # Expected error
            else:
                response.failure(f"Unexpected status: {response.status_code}")

        # Invalid request body
        with self.client.post(
            "/seller/pricing/suggest",
            json={"invalid": "data"},
            catch_response=True,
        ) as response:
            if response.status_code >= 400:
                response.success()  # Expected validation error
            else:
                response.failure("Should have returned validation error")


class HighLoadUser(HttpUser):
    """Heavy user with more aggressive request patterns."""

    wait_time = between(0.5, 1.5)

    @task(10)
    def hammer_listings(self):
        """Constantly request listings (stress test)."""
        with self.client.get(
            "/listings",
            params={"limit": 100},
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Stress test failed: {response.status_code}")


# ============================================================================
# EVENT HANDLERS & MONITORING
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called at test start."""
    print(f"\n{'='*60}")
    print(f"Load test started at {datetime.now()}")
    print(f"Target: {environment.host}")
    print(f"{'='*60}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called at test stop."""
    print(f"\n{'='*60}")
    print(f"Load test stopped at {datetime.now()}")
    print(f"{'='*60}\n")

    # Print summary
    print("\nTest Results Summary:")
    print("-" * 60)

    stats = environment.stats
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Success Rate: {(1 - stats.total.failure_rate) * 100:.1f}%")
    print(f"Avg Response Time: {stats.total.avg_response_time:.0f}ms")
    print(f"Min Response Time: {stats.total.min_response_time:.0f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.0f}ms")
    print(f"RPS: {stats.total.total_rps:.1f}")


# ============================================================================
# LOAD TEST SCENARIOS
# ============================================================================

"""
Load Test Scenarios:

1. BASELINE (Normal Load):
   locust -f load_test.py --host http://localhost:8000 -u 10 -r 2 -t 5m
   - 10 users ramping up at 2 users/second
   - Duration: 5 minutes
   Expected: < 500ms p95 latency, < 1% error rate

2. SUSTAINED (Standard Load):
   locust -f load_test.py --host http://localhost:8000 -u 50 -r 5 -t 10m
   - 50 users ramping up at 5 users/second
   - Duration: 10 minutes
   Expected: < 1000ms p95 latency, < 1% error rate

3. PEAK (High Load):
   locust -f load_test.py --host http://localhost:8000 -u 200 -r 20 -t 15m
   - 200 users ramping up at 20 users/second
   - Duration: 15 minutes
   Expected: < 2000ms p95 latency, < 5% error rate

4. STRESS (Maximum Load):
   locust -f load_test.py --host http://localhost:8000 -u 500 -r 50 -t 20m
   - 500 users ramping up at 50 users/second
   - Duration: 20 minutes
   - Identify breaking point

5. SPIKE (Sudden Traffic):
   locust -f load_test.py --host http://localhost:8000 -u 100 -r 100 -t 5m
   - 100 users instant ramp up
   - Duration: 5 minutes
   - Test sudden traffic handling

Web UI:
   locust -f load_test.py --host http://localhost:8000 --web
   - Opens web interface at http://localhost:8089

Headless (No UI):
   locust -f load_test.py --host http://localhost:8000 -u 50 -r 5 --headless -t 10m --csv results
"""

# Example Pytest integration for CI/CD
def test_load_performance():
    """Test performance meets SLOs."""
    # This would be integrated into CI/CD pipeline
    # Run load test and check results
    pass
