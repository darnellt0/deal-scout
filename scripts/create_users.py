#!/usr/bin/env python3
"""
Create user accounts for Deal Scout testing.
Run this script to create accounts for you and your wife.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def create_user(username, email, password, role="seller"):
    """Create a new user account."""
    url = f"{BASE_URL}/auth/register"
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "role": role,
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        print(f"✅ Created user: {username}")
        print(f"   Email: {email}")
        print(f"   Role: {role}")
        print(f"   Access Token: {data['access_token'][:50]}...")
        print(f"   User ID: {data['user']['id']}")
        print()

        return data
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to backend. Make sure the backend is running:")
        print("   docker compose up -d backend")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        error_data = e.response.json()
        print(f"❌ Error creating user {username}: {error_data.get('detail', 'Unknown error')}")
        return None

def login_user(username, password):
    """Login and get access token."""
    url = f"{BASE_URL}/auth/login"
    payload = {
        "username": username,
        "password": password,
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        print(f"✅ Logged in as: {username}")
        print(f"   Access Token: {data['access_token'][:50]}...")
        print()

        return data
    except requests.exceptions.HTTPError as e:
        error_data = e.response.json()
        print(f"❌ Login failed: {error_data.get('detail', 'Unknown error')}")
        return None

def main():
    print("=" * 70)
    print("Deal Scout - Create User Accounts")
    print("=" * 70)
    print()

    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=2)
        print("✅ Backend is running")
        print()
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running!")
        print()
        print("Start the backend with:")
        print("  cd /home/user/deal-scout")
        print("  docker compose up -d backend")
        print()
        sys.exit(1)

    # Create first user account (for you)
    print("Creating Account #1 (Primary Seller)...")
    user1 = create_user(
        username="seller1",
        email="seller1@dealscout.local",
        password="Password123!",
        role="seller"
    )

    # Create second user account (for your wife)
    print("Creating Account #2 (Secondary Seller)...")
    user2 = create_user(
        username="seller2",
        email="seller2@dealscout.local",
        password="Password123!",
        role="seller"
    )

    print("=" * 70)
    print("✅ Setup Complete!")
    print("=" * 70)
    print()
    print("You can now login with:")
    print()
    print("Account #1:")
    print(f"  Username: seller1")
    print(f"  Password: Password123!")
    print(f"  URL: http://localhost:3000")
    print()
    print("Account #2:")
    print(f"  Username: seller2")
    print(f"  Password: Password123!")
    print(f"  URL: http://localhost:3000")
    print()

    if user1:
        print("Save these tokens for API testing:")
        print()
        print(f"USER1_TOKEN=\"{user1['access_token']}\"")
        if user2:
            print(f"USER2_TOKEN=\"{user2['access_token']}\"")
        print()

    print("To use in curl commands:")
    print('  curl -H "Authorization: Bearer $USER1_TOKEN" http://localhost:8000/deal-alert-rules')
    print()

if __name__ == "__main__":
    main()
