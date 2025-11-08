#!/bin/bash
set -e

echo "========================================="
echo "Deal Scout - First User Setup"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker Compose is running
echo "🔍 Checking if services are running..."
if ! docker compose ps | grep -q "backend.*Up"; then
    echo -e "${RED}❌ Backend service is not running!${NC}"
    echo ""
    echo "Please start the services first:"
    echo "  docker compose up -d"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Services are running${NC}"
echo ""

# Run migrations
echo "🗄️  Running database migrations..."
docker compose exec -T backend alembic upgrade head

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migrations completed${NC}"
else
    echo -e "${RED}❌ Migration failed!${NC}"
    echo "Check logs with: docker compose logs backend"
    exit 1
fi
echo ""

# Check if users exist
echo "👥 Checking for existing users..."
USER_COUNT=$(docker compose exec -T postgres psql -U deals -d deals -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$USER_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Database already has $USER_COUNT user(s)${NC}"
    echo ""
    read -p "Do you want to create another user? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 0
    fi
fi

# Prompt for user details
echo ""
echo "📝 Create your admin user"
echo "========================="
echo ""

read -p "Username: " USERNAME
read -p "Email: " EMAIL
read -s -p "Password: " PASSWORD
echo ""
read -s -p "Confirm Password: " PASSWORD_CONFIRM
echo ""
echo ""

if [ "$PASSWORD" != "$PASSWORD_CONFIRM" ]; then
    echo -e "${RED}❌ Passwords don't match!${NC}"
    exit 1
fi

read -p "First Name (optional): " FIRST_NAME
read -p "Last Name (optional): " LAST_NAME

# Create user via API
echo ""
echo "🚀 Creating user..."

RESPONSE=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$USERNAME\",
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\",
    \"first_name\": \"${FIRST_NAME:-User}\",
    \"last_name\": \"${LAST_NAME:-Admin}\"
  }" 2>&1)

if echo "$RESPONSE" | grep -q '"id"'; then
    echo -e "${GREEN}✅ User created successfully!${NC}"
    echo ""
    echo "User Details:"
    echo "$RESPONSE" | jq '.'
    echo ""
    echo -e "${GREEN}🎉 You can now login at http://localhost:3000${NC}"
    echo ""
    echo "Login credentials:"
    echo "  Username: $USERNAME"
    echo "  Password: [the password you entered]"
    echo ""
elif echo "$RESPONSE" | grep -q "Connection refused"; then
    echo -e "${RED}❌ Cannot connect to backend!${NC}"
    echo ""
    echo "The backend service might not be fully started yet."
    echo "Wait 30 seconds and try again, or check logs:"
    echo "  docker compose logs backend"
else
    echo -e "${RED}❌ Failed to create user${NC}"
    echo ""
    echo "Response from server:"
    echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
    echo ""
    echo "Common issues:"
    echo "  - Username or email already exists"
    echo "  - Password doesn't meet requirements"
    echo "  - Backend service not ready"
fi

echo ""
echo "========================================="
