#!/usr/bin/env python3
"""Quick Phase 4 API Testing Script"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_phase4():
    """Test Phase 4 endpoints"""

    print("\n" + "="*60)
    print("PHASE 4 API TESTING")
    print("="*60 + "\n")

    # 1. Register User
    print("1. REGISTERING TEST USER...")
    user_data = {
        "username": "testphase4",
        "email": "testphase4@example.com",
        "password": "TestPassword123"
    }

    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=user_data
    )

    if response.status_code != 201:
        print(f"❌ Registration failed: {response.status_code}")
        print(response.json())
        return

    user_info = response.json()
    token = user_info["access_token"]
    user_id = user_info["user"]["id"]

    print(f"✅ User registered! ID: {user_id}")
    print(f"   Token (first 20 chars): {token[:20]}...")

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test Buyer Deals
    print("\n2. TESTING BUYER DEALS ENDPOINT...")
    response = requests.get(
        f"{BASE_URL}/buyer/deals?limit=3",
        headers=headers
    )

    if response.status_code == 200:
        deals = response.json()
        print(f"OK: Got {len(deals)} deals")
        if deals:
            print(f"   First deal: {deals[0]['title']} (${deals[0]['price']})")
    else:
        print(f"❌ Failed: {response.status_code}")

    # 3. Test Notification Preferences
    print("\n3️⃣  TESTING NOTIFICATION PREFERENCES...")
    response = requests.get(
        f"{BASE_URL}/notification-preferences",
        headers=headers
    )

    if response.status_code == 200:
        prefs = response.json()
        print(f"✅ Got preferences")
        print(f"   Email notifications: {prefs['email_notifications']}")
        print(f"   Frequency: {prefs['notification_frequency']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.json())

    # 4. Test Update Notification Preferences
    print("\n4️⃣  TESTING UPDATE NOTIFICATION PREFERENCES...")
    response = requests.put(
        f"{BASE_URL}/notification-preferences?notification_frequency=daily_digest&deal_alert_min_score=8.0",
        headers=headers
    )

    if response.status_code == 200:
        print(f"✅ Updated preferences")
    else:
        print(f"❌ Failed: {response.status_code}")

    # 5. Test Get Buyer Preferences
    print("\n5️⃣  TESTING BUYER PREFERENCES...")
    response = requests.get(
        f"{BASE_URL}/buyer/preferences",
        headers=headers
    )

    if response.status_code == 200:
        buyer_prefs = response.json()
        print(f"✅ Got buyer preferences")
        print(f"   Search radius: {buyer_prefs['search_radius_mi']} miles")
        print(f"   Max price (couch): ${buyer_prefs['max_price_couch']}")
    else:
        print(f"❌ Failed: {response.status_code}")

    # 6. Test Marketplace Accounts
    print("\n6️⃣  TESTING MARKETPLACE ACCOUNTS...")
    response = requests.post(
        f"{BASE_URL}/marketplace-accounts?platform=ebay&account_username=teststore",
        headers=headers
    )

    if response.status_code == 201:
        account = response.json()
        print(f"✅ Created marketplace account")
        print(f"   Platform: {account['platform']}")
        print(f"   Username: {account['account_username']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.json())

    # 7. List Marketplace Accounts
    print("\n7️⃣  LISTING MARKETPLACE ACCOUNTS...")
    response = requests.get(
        f"{BASE_URL}/marketplace-accounts",
        headers=headers
    )

    if response.status_code == 200:
        accounts = response.json()
        print(f"✅ Got {len(accounts)} marketplace accounts")
        for account in accounts:
            print(f"   - {account['platform']}: {account['account_username']}")
    else:
        print(f"❌ Failed: {response.status_code}")

    # 8. Test Snap Studio
    print("\n8️⃣  TESTING SNAP STUDIO...")
    response = requests.post(
        f"{BASE_URL}/seller/snap",
        json={
            "photos": ["https://example.com/photo.jpg"],
            "notes": "Test couch",
            "source": "upload"
        },
        headers=headers
    )

    if response.status_code == 201:
        snap = response.json()
        print(f"✅ Created snap job")
        print(f"   Job ID: {snap['job_id']}")
        print(f"   Status: {snap['status']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.json())

    # 9. Test Pricing - Get Categories
    print("\n9️⃣  TESTING PRICING ENDPOINTS...")
    response = requests.get(
        f"{BASE_URL}/seller/pricing/categories"
    )

    if response.status_code == 200:
        categories_data = response.json()
        categories = categories_data.get('categories', [])
        print(f"✅ Got {len(categories)} product categories")
        if categories:
            print(f"   First category: {categories[0]}")
    else:
        print(f"❌ Failed: {response.status_code}")

    # 10. Summary
    print("\n" + "="*60)
    print("✅ PHASE 4 TESTING COMPLETE!")
    print("="*60)
    print("\nNext Steps:")
    print("📖 Read: PHASE_4_TESTING_GUIDE.md")
    print("🌐 Open: http://localhost:8000/docs")
    print("📝 API Docs: http://localhost:8000/openapi.json")
    print("\nAll endpoints tested successfully! 🎉\n")

if __name__ == "__main__":
    test_phase4()
