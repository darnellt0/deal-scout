#!/usr/bin/env python3
"""
Quick script to create an admin user for Deal Scout.
Run with: python create_admin.py
"""

import sys
import os
from getpass import getpass

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.models import User, UserRole
from app.core.auth import get_password_hash
from app.config import get_settings

def create_admin_user():
    """Create an admin user interactively."""

    print("=" * 50)
    print("Deal Scout - Admin User Creation")
    print("=" * 50)
    print()

    # Get database connection
    settings = get_settings()
    engine = create_engine(str(settings.database_url))

    # Get user details
    username = input("Username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        return

    email = input("Email: ").strip()
    if not email:
        print("❌ Email cannot be empty")
        return

    password = getpass("Password: ")
    if len(password) < 8:
        print("❌ Password must be at least 8 characters")
        return

    password_confirm = getpass("Confirm Password: ")
    if password != password_confirm:
        print("❌ Passwords don't match")
        return

    first_name = input("First Name (optional): ").strip() or "Admin"
    last_name = input("Last Name (optional): ").strip() or "User"

    # Create user
    try:
        with Session(engine) as session:
            # Check if username exists
            existing = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()

            if existing:
                print(f"❌ User with username '{username}' or email '{email}' already exists")
                return

            # Create new user
            user = User(
                username=username,
                email=email,
                password_hash=get_password_hash(password),
                first_name=first_name,
                last_name=last_name,
                role=UserRole.admin,
                is_active=True,
                is_verified=True
            )

            session.add(user)
            session.commit()
            session.refresh(user)

            print()
            print("✅ Admin user created successfully!")
            print()
            print(f"User ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role.value}")
            print()
            print("🎉 You can now login at http://localhost:3000")

    except Exception as e:
        print(f"❌ Error creating user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_admin_user()
