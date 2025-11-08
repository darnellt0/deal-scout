-- Run on Neon dashboard or psql to promote user to seller
-- This is needed if the user role comes back as "buyer" instead of "seller"

UPDATE users SET role='seller', is_verified=true WHERE username='darnell';

-- Verify the update
SELECT id, username, role, email, is_verified FROM users WHERE username='darnell';
