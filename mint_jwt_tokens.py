#!/usr/bin/env python3
"""
JWT Token Generator for Phase 4 Testing

This script helps you quickly generate JWT tokens for different user roles
without needing to go through the full registration flow.

Usage:
    python mint_jwt_tokens.py              # Interactive menu
    python mint_jwt_tokens.py --buyer      # Generate buyer token
    python mint_jwt_tokens.py --seller     # Generate seller token
    python mint_jwt_tokens.py --admin      # Generate admin token
    python mint_jwt_tokens.py --user 123 --role seller  # Custom user ID and role

Requirements:
    pip install PyJWT
"""

import jwt
import json
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Configuration - Match your backend settings
JWT_SECRET = "your-secret-key-here"  # MUST match backend .env JWT_SECRET_KEY
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = 24

# Sample users for quick testing
SAMPLE_USERS = {
    "buyer": {
        "user_id": 1,
        "username": "testbuyer",
        "email": "buyer@example.com",
        "role": "buyer"
    },
    "seller": {
        "user_id": 2,
        "username": "testseller",
        "email": "seller@example.com",
        "role": "seller"
    },
    "admin": {
        "user_id": 999,
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin"
    }
}


def generate_token(user_id: int, username: str, email: str, role: str) -> str:
    """
    Generate a JWT token with the given user details.

    Args:
        user_id: Numeric user ID
        username: Username string
        email: Email address
        role: User role (buyer, seller, admin)

    Returns:
        JWT token string
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token: str) -> dict:
    """
    Decode and display token contents (for debugging).

    Args:
        token: JWT token string

    Returns:
        Decoded payload dictionary
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError as e:
        return {"error": f"Invalid token: {str(e)}"}


def print_token_info(token: str, role: str):
    """Pretty-print token information."""
    print("\n" + "="*70)
    print(f"✅ TOKEN GENERATED FOR: {role.upper()}")
    print("="*70)

    # Decode to show payload
    payload = decode_token(token)
    if "error" not in payload:
        print("\nToken Payload:")
        print(json.dumps(payload, indent=2, default=str))

    print("\nToken (for use in headers):")
    print(f"Authorization: Bearer {token}")

    print("\nTo use in VS Code REST Client:")
    print(f"@token = {token}")

    print("\nTo use in curl:")
    print(f'curl -H "Authorization: Bearer {token}" http://localhost:8000/auth/me')

    print("\nExpires in: {} hours".format(TOKEN_EXPIRATION_HOURS))
    print("="*70 + "\n")


def interactive_menu():
    """Show interactive menu for token generation."""
    print("\n" + "="*70)
    print("DEAL SCOUT - JWT TOKEN GENERATOR")
    print("="*70)
    print("\nQuick token generation for Phase 4 testing")
    print("\nChoose an option:")
    print("  1. Generate BUYER token")
    print("  2. Generate SELLER token")
    print("  3. Generate ADMIN token")
    print("  4. Generate CUSTOM token")
    print("  5. Decode existing token")
    print("  6. Exit")
    print("\n" + "-"*70)

    choice = input("Enter choice (1-6): ").strip()

    if choice == "1":
        user = SAMPLE_USERS["buyer"]
        token = generate_token(user["user_id"], user["username"], user["email"], user["role"])
        print_token_info(token, "BUYER")
        return True

    elif choice == "2":
        user = SAMPLE_USERS["seller"]
        token = generate_token(user["user_id"], user["username"], user["email"], user["role"])
        print_token_info(token, "SELLER")
        return True

    elif choice == "3":
        user = SAMPLE_USERS["admin"]
        token = generate_token(user["user_id"], user["username"], user["email"], user["role"])
        print_token_info(token, "ADMIN")
        return True

    elif choice == "4":
        print("\n--- Custom Token Generation ---")
        try:
            user_id = int(input("Enter user ID (number): "))
            username = input("Enter username: ").strip()
            email = input("Enter email: ").strip()
            role = input("Enter role (buyer/seller/admin): ").strip().lower()

            if role not in ["buyer", "seller", "admin"]:
                print("❌ Invalid role. Must be: buyer, seller, or admin")
                return True

            token = generate_token(user_id, username, email, role)
            print_token_info(token, role)
            return True
        except ValueError:
            print("❌ Invalid input. User ID must be a number.")
            return True

    elif choice == "5":
        token = input("Paste token to decode: ").strip()
        payload = decode_token(token)

        if "error" in payload:
            print(f"\n❌ Error: {payload['error']}")
        else:
            print("\n✅ Token Details:")
            print(json.dumps(payload, indent=2, default=str))

        return True

    elif choice == "6":
        print("\nGoodbye! 👋")
        return False

    else:
        print("❌ Invalid choice. Please enter 1-6.")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="JWT Token Generator for Deal Scout Phase 4 Testing"
    )
    parser.add_argument(
        "--buyer",
        action="store_true",
        help="Generate a buyer token"
    )
    parser.add_argument(
        "--seller",
        action="store_true",
        help="Generate a seller token"
    )
    parser.add_argument(
        "--admin",
        action="store_true",
        help="Generate an admin token"
    )
    parser.add_argument(
        "--user",
        type=int,
        help="Custom user ID"
    )
    parser.add_argument(
        "--username",
        default="testuser",
        help="Custom username (default: testuser)"
    )
    parser.add_argument(
        "--email",
        default="test@example.com",
        help="Custom email (default: test@example.com)"
    )
    parser.add_argument(
        "--role",
        default="buyer",
        choices=["buyer", "seller", "admin"],
        help="User role (default: buyer)"
    )
    parser.add_argument(
        "--decode",
        help="Decode an existing token"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=True,
        help="Run in interactive mode (default if no args)"
    )

    args = parser.parse_args()

    # If decode flag is set
    if args.decode:
        payload = decode_token(args.decode)
        if "error" in payload:
            print(f"❌ Error: {payload['error']}")
            sys.exit(1)
        else:
            print("✅ Decoded Token:")
            print(json.dumps(payload, indent=2, default=str))
        sys.exit(0)

    # If any specific role is requested
    if args.buyer or args.seller or args.admin or args.user:
        role = "buyer"
        user_id = 1
        username = args.username
        email = args.email

        if args.seller:
            role = "seller"
            user_id = args.user or 2
        elif args.admin:
            role = "admin"
            user_id = args.user or 999
        elif args.buyer:
            role = "buyer"
            user_id = args.user or 1
        elif args.user:
            user_id = args.user
            role = args.role

        token = generate_token(user_id, username, email, role)
        print_token_info(token, role)
        sys.exit(0)

    # Otherwise, run interactive mode
    print("\n🔑 Starting JWT Token Generator...")

    while True:
        try:
            if not interactive_menu():
                break
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye! 👋\n")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue


if __name__ == "__main__":
    main()
