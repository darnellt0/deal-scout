# Security Guidelines - Deal Scout

## Security Overview

This document outlines security best practices, threat mitigations, and compliance considerations for Deal Scout.

## Secure Development Practices

### Credential Management

**DO:**
- Store all credentials in environment variables or secure vaults
- Use `.env.production` template with placeholder values
- Rotate API keys and database credentials monthly
- Use managed services' built-in credential rotation where available

**DON'T:**
- Commit credentials to git or version control
- Use default/hardcoded passwords
- Share credentials via email or chat
- Log sensitive data (API keys, tokens, passwords)

### Input Validation

All user input must be validated and sanitized:

```python
from app.core.validation import (
    validate_email,
    validate_price,
    validate_url,
    validate_string_length,
    sanitize_html,
)

# Examples of proper validation
try:
    email = validate_email(user_input)
    price = validate_price(user_input, min_price=0, max_price=1000000)
    url = validate_url(listing_url)
    title = validate_string_length(title, min_length=3, max_length=255)
    description = sanitize_html(description)
except ValidationError as e:
    return {"error": str(e)}, 400
```

### Database Security

1. **Connection Security**:
   - Always use TLS/SSL for database connections
   - Store connection strings in environment variables
   - Use connection pooling with appropriate limits

2. **Query Security**:
   - Use parameterized queries (SQLAlchemy ORM does this automatically)
   - Never concatenate user input into SQL
   - Use SQLAlchemy's `text()` function carefully

3. **Access Control**:
   - Use least privilege for database users
   - Create read-only user for analytics queries
   - Audit database access logs

### Authentication & Authorization

Current system uses environment-based configuration. For future auth:

```python
# Suggested JWT-based authentication
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    token = credentials.credentials
    # Verify JWT signature
    # Check token expiration
    # Validate claims
    return decoded_token
```

### API Security

1. **CORS Configuration**:
   ```python
   # Only allow specific origins in production
   CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
   ```

2. **Rate Limiting** (to implement):
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address

   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter

   @app.get("/listings")
   @limiter.limit("30/minute")
   async def get_listings(request: Request):
       ...
   ```

3. **Security Headers**:
   - X-Content-Type-Options: nosniff (✓ implemented)
   - X-Frame-Options: DENY (✓ implemented)
   - X-XSS-Protection: 1; mode=block (✓ implemented)
   - Strict-Transport-Security (✓ implemented)
   - Content-Security-Policy (✓ implemented)

### Error Handling

**DO:**
- Log detailed errors server-side
- Return generic error messages to clients
- Never expose stack traces in API responses
- Track errors in monitoring system

**DON'T:**
- Expose sensitive paths or configuration
- Include database error details in responses
- Log passwords, tokens, or API keys

Example:
```python
try:
    result = perform_operation()
except DatabaseError as e:
    logger.exception("Database error during operation")  # Detailed log
    return {"error": "Operation failed"}, 500  # Generic response
```

## Third-Party Service Security

### OpenAI
- Use API key rotation
- Monitor API usage and costs
- Review rate limits

### eBay OAuth
- Store tokens securely in database (encrypted)
- Implement token refresh logic
- Validate token scopes

### Twilio
- Validate phone numbers before sending
- Implement rate limiting per phone number
- Monitor SMS costs

### Email (SMTP)
- Use TLS/SSL (✓ configured)
- Authenticate with credentials (✓ configured)
- Implement SPF, DKIM, DMARC for domain

### Discord Webhooks
- Store webhook URLs securely (encrypted)
- Use HTTPS only
- Rotate webhooks if compromised

## Data Security

### At Rest
- Database encryption: Use RDS/Cloud SQL encryption
- S3 encryption: Enable default encryption
- Backup encryption: Encrypt database snapshots
- Log file encryption: Enable CloudWatch Logs encryption

### In Transit
- HTTPS only (HTTP redirects to HTTPS)
- TLS 1.2 minimum
- Certificate pinning (optional, for high-security)

### Data Retention
- User data: Retention policy per user preferences
- Logs: 30 days retention
- Backups: 7-30 days depending on tier
- Deletion: Secure erasure (3-pass overwrite)

### PII Handling
- Minimize collection of personal data
- Encrypt PII in database
- Hash sensitive identifiers
- Implement right-to-be-forgotten

## Infrastructure Security

### Network
- VPC isolation of database and cache
- Security groups restrict ports
- No public database access
- API accessible only via load balancer

### Compute
- Container image scanning for vulnerabilities
- Run as non-root user
- Resource limits (memory, CPU)
- No privileged containers

### Secrets Management

**Option 1: AWS Secrets Manager**
```bash
# Store secrets
aws secretsmanager create-secret \
  --name deal-scout/prod \
  --secret-string file://production.json

# Retrieve in application
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='deal-scout/prod')
```

**Option 2: HashiCorp Vault**
```bash
# Store secrets
vault kv put secret/deal-scout/prod \
  DATABASE_URL="..." \
  OPENAI_API_KEY="..."

# Retrieve in application
import hvac
client = hvac.Client()
secret = client.secrets.kv.read_secret_version(path='deal-scout/prod')
```

## Dependency Management

### Vulnerability Scanning

```bash
# Scan for known vulnerabilities
pip install safety
safety check

# Automated scanning with Snyk
snyk test

# Regular updates
pip install --upgrade pip setuptools wheel
pip install --upgrade -r requirements.txt
```

### Dependency Pinning

```
# requirements.txt should pin versions
fastapi==0.110.0
sqlalchemy==2.0.23
celery==5.3.4
```

## Compliance

### GDPR (If serving EU users)
- ✓ Data minimization
- ✓ Encryption in transit
- ✓ Access logging
- TODO: Right to erasure implementation
- TODO: Data portability implementation
- TODO: Privacy policy

### PCI DSS (If handling payments)
- Encryption of payment data
- Tokenization of payment info
- Regular security audits
- Firewalled network
- User access management

## Incident Response

### Breach Notification Process

1. **Detect**: Monitoring alerts on suspicious activity
2. **Contain**: Isolate affected systems
3. **Investigate**: Determine scope and impact
4. **Notify**: Inform users/regulators within required timeframe
5. **Remediate**: Fix vulnerability and deploy fix
6. **Review**: Post-incident review and improvements

### Security Contacts

- Security Team Lead: [contact]
- On-Call: [escalation phone/email]
- Incident Hotline: [number]

## Security Checklist for Each Release

- [ ] No hardcoded secrets or credentials
- [ ] All dependencies up to date
- [ ] Security tests pass (`pytest --security`)
- [ ] Input validation on all endpoints
- [ ] Error messages don't expose sensitive info
- [ ] Database migrations tested
- [ ] API rate limiting working
- [ ] Logging doesn't capture sensitive data
- [ ] HTTPS/TLS enabled
- [ ] Security headers present
- [ ] Database backed up
- [ ] Secrets rotated

## Reporting Security Vulnerabilities

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. Email security@your-domain.com with details
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (optional)

We aim to respond within 24 hours and provide updates every 72 hours.

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/faq/security.html)
- [12 Factor App](https://12factor.net/)
