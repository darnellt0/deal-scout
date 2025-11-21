#!/usr/bin/env python3
"""Update demo user role to seller."""

import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Add the app directory to the path so we can import models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from core.models import User, UserRole

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/deal_scout"
)

def update_demo_user_role():
    """Update the demo user's role to seller."""
    engine = create_engine(DATABASE_URL)

    with Session(engine) as session:
        # Find the demo user
        demo_user = session.query(User).filter(User.username == "demo").first()

        if demo_user:
            print(f"Found demo user: {demo_user.username} (current role: {demo_user.role.value})")
            demo_user.role = UserRole.seller
            session.commit()
            print(f"Updated demo user role to: {demo_user.role.value}")
        else:
            print("Demo user not found. User may not be registered yet.")
            sys.exit(1)

if __name__ == "__main__":
    update_demo_user_role()
