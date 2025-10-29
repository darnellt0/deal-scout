#!/usr/bin/env python3
"""
Cross-platform diagnostics tool for deal-scout development stack.
Checks backend health, database, and Redis connectivity.
"""

import json
import socket
import sys
import time
from typing import Dict, Any, List, Tuple

try:
    import requests
except ImportError:
    print("ERROR: 'requests' module not found. Install it with: pip install requests")
    sys.exit(1)


def check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a port is listening on the given host."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except (socket.timeout, OSError, ConnectionRefusedError):
        return False
    finally:
        try:
            s.close()
        except OSError:
            pass


def check_backend_port() -> Tuple[bool, str]:
    """Check if backend is listening on port 8000."""
    if check_port("localhost", 8000):
        return True, "Backend port 8000 is listening"
    return False, "Backend port 8000 not listening (is container running?)"


def check_health_endpoint() -> Tuple[bool, Dict[str, Any]]:
    """Check /health endpoint response."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=3)
        data = response.json() if response.text else {}
        if response.status_code == 200:
            return True, data
        return False, {"status_code": response.status_code, "error": "Non-200 response"}
    except requests.exceptions.Timeout:
        return False, {"error": "Request timeout"}
    except requests.exceptions.ConnectionError:
        return False, {"error": "Connection refused"}
    except Exception as e:
        return False, {"error": str(e)}


def check_ping_endpoint() -> Tuple[bool, Dict[str, Any]]:
    """Check /ping endpoint response."""
    try:
        response = requests.get("http://localhost:8000/ping", timeout=3)
        data = response.json() if response.text else {}
        if response.status_code == 200:
            return True, data
        return False, {"status_code": response.status_code}
    except Exception:
        return False, None


def main() -> int:
    """Run all diagnostics and return exit code."""
    print("\n" + "=" * 60)
    print("Deal Scout Development Stack Diagnostics")
    print("=" * 60 + "\n")

    all_checks: Dict[str, Tuple[bool, Any]] = {}
    errors: List[str] = []

    # Check 1: Backend port
    print("1. Backend Connectivity")
    ok, msg = check_backend_port()
    all_checks["backend_port"] = ok
    print(f"   {'✓' if ok else '✗'} {msg}")
    if not ok:
        errors.append("Backend is not running. Start with: docker compose up -d")

    # Check 2: Health endpoint
    print("\n2. Health Check Endpoint")
    ok, data = check_health_endpoint()
    all_checks["health_endpoint"] = ok
    if ok:
        print(f"   ✓ GET /health returned 200")
        print(f"     - DB: {'OK' if data.get('db') else 'FAILED'}")
        print(f"     - Redis: {'OK' if data.get('redis') else 'FAILED'}")
        print(f"     - Queue depth: {data.get('queue_depth', 'N/A')}")
        if not data.get("ok"):
            errors.append("Health check reports degraded status (db or redis down)")
    else:
        print(f"   ✗ GET /health failed: {data.get('error', 'Unknown error')}")
        errors.append("Health endpoint not responding")

    # Check 3: Ping endpoint
    print("\n3. Ping Endpoint")
    ok, data = check_ping_endpoint()
    all_checks["ping_endpoint"] = ok
    if ok:
        print(f"   ✓ GET /ping responded")
    else:
        print(f"   ✗ GET /ping failed")

    # Check 4: Database port
    print("\n4. Database (Postgres)")
    db_ok = check_port("localhost", 5432)
    all_checks["postgres_port"] = db_ok
    print(f"   {'✓' if db_ok else '✗'} Port 5432 {'listening' if db_ok else 'not listening'}")
    if not db_ok:
        errors.append("Postgres is not running. Check: docker compose logs postgres")

    # Check 5: Redis port
    print("\n5. Redis Cache")
    redis_ok = check_port("localhost", 6379)
    all_checks["redis_port"] = redis_ok
    print(f"   {'✓' if redis_ok else '✗'} Port 6379 {'listening' if redis_ok else 'not listening'}")
    if not redis_ok:
        errors.append("Redis is not running. Check: docker compose logs redis")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    success = len(errors) == 0
    status = "✓ All checks passed!" if success else f"✗ {len(errors)} check(s) failed"
    print(f"\nStatus: {status}\n")

    if errors:
        print("Issues found:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print()

    # Output JSON for machine parsing
    output = {
        "success": success,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checks": all_checks,
        "errors": errors,
    }

    print("Detailed results (JSON):")
    print(json.dumps(output, indent=2))
    print()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
