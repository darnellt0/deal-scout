# Deal Scout - Seller Cross-Post MVP

**One Photo → Multiple Marketplaces**

Deal Scout is a seller-first marketplace assistant that lets you upload a photo of an item and automatically cross-post it to eBay, Facebook Marketplace, and OfferUp with AI-generated listings.

## 🎯 What This Does

1. **Upload a photo** of your item
2. **AI detects** the item, generates title/description, suggests pricing
3. **One-click publish** to eBay, Facebook Marketplace, and OfferUp
4. **Track status** of all your cross-posts in one dashboard

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- (Optional) AWS S3 bucket for image hosting
- (Optional) Marketplace API credentials (eBay, Facebook, OfferUp)

### 1. Clone and Configure

```bash
git clone <repo-url>
cd deal-scout
cp .env.example .env
```

Edit `.env` with your API keys (optional for demo mode):

```bash
# Required for AI features
ANTHROPIC_API_KEY=your-key-here
# OR
OPENAI_API_KEY=your-key-here

# Optional - S3 for image hosting (recommended for production)
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET=your-bucket-name

# Optional - Marketplace credentials
EBAY_APP_ID=your-app-id
EBAY_CERT_ID=your-cert-id
EBAY_DEV_ID=your-dev-id
```

### 2. Launch

```bash
docker compose up --build
```

Services start on:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Use It

1. Go to http://localhost:3000
2. Click "Start Selling"
3. Upload photos
4. Review AI-generated listing
5. Select marketplaces (eBay/Facebook/OfferUp)
6. Publish!

## 📦 Project Structure

```
deal-scout/
├── frontend/           # Next.js app (seller UI)
│   ├── app/
│   │   ├── page.tsx          # Landing page
│   │   └── seller/page.tsx   # Main seller dashboard
│   └── components/
│       ├── UploadForm.tsx
│       └── QuickListingModal.tsx
│
├── backend/            # FastAPI + Celery
│   ├── app/
│   │   ├── seller/           # Seller workflows
│   │   │   ├── snap.py       # Photo processing
│   │   │   ├── post.py       # Cross-posting
│   │   │   └── pricing.py    # Price suggestions
│   │   ├── market/           # Marketplace clients
│   │   │   ├── ebay_client.py
│   │   │   ├── facebook_client.py
│   │   │   └── offerup_client.py
│   │   ├── services/         # New service layer
│   │   │   ├── image_storage.py    # S3/local upload
│   │   │   └── cross_posting.py    # Orchestrator
│   │   ├── vision/           # AI item detection
│   │   │   ├── claude_vision.py
│   │   │   └── detector.py
│   │   ├── tasks/            # Celery tasks
│   │   │   ├── process_snap.py     # Photo processing
│   │   │   ├── reconcile_sales.py  # Sync sales
│   │   │   └── refresh_comps.py    # Update pricing
│   │   └── routes/           # API routes
│   │       ├── my_items.py
│   │       ├── cross_posts.py
│   │       └── marketplace_accounts.py
│   └── alembic/        # Database migrations
│
├── archive/            # Parked buyer features
│   └── README.md       # Restoration guide
│
├── docker-compose.yml
└── .env.example
```

## 🔑 Core Features

### ✅ Implemented (Seller MVP)

- **Snap Studio**: Upload photos → AI detection → auto-generated listings
- **Claude Vision**: Real item detection with category, condition, attributes
- **Cross-posting**: Publish to eBay, Facebook, OfferUp simultaneously
- **OAuth Integration**: Connect marketplace accounts
- **Price Suggestions**: Comp-based pricing from eBay sold listings
- **Status Tracking**: Monitor all cross-posts in one dashboard
- **Image Cleanup**: Auto-brighten and enhance photos
- **Listing Generation**: AI-written titles and descriptions

### 🔒 Parked (Buyer Features)

Buyer-focused features are archived in `/archive` with restoration instructions:
- Marketplace scanning for deals
- Deal alerts and notifications
- Price drop monitoring
- Buyer dashboard

**To restore**: See `/archive/README.md`

## 🛠 Configuration

### Feature Flags

Control optional features in `.env`:

```bash
FEATURE_BUYER=false          # Buyer features (parked)
FEATURE_BG_CLEAN=false       # Background removal (experimental)
FEATURE_ADV_VISION=false     # Advanced vision features
FEATURE_LIVE_PRICING=false   # Live price updates
```

### Image Storage

**Local (default for development):**
- Images stored in `/backend/static/uploads`
- Served at `/static/uploads/<filename>`

**S3 (recommended for production):**
- Set `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET`
- Images auto-uploaded with public ACL
- URLs like `https://bucket.s3.region.amazonaws.com/images/file.jpg`

### Marketplace Setup

#### eBay
1. Create developer account at https://developer.ebay.com
2. Get App ID, Cert ID, Dev ID
3. Run OAuth flow: `GET /ebay/authorize`
4. Exchange code: `POST /ebay/exchange`

#### Facebook Marketplace
1. Create Meta app at https://developers.facebook.com
2. Enable Marketplace API
3. Get App ID and Secret
4. Run OAuth: `GET /facebook-oauth/authorize`

#### OfferUp
1. Contact OfferUp for API access
2. Get Client ID and Secret
3. Run OAuth: `GET /offerup-oauth/authorize`

## 📡 API Endpoints

### Seller Endpoints

```bash
# Snap Studio
POST   /seller/snap              # Create snap job (upload photos)
GET    /seller/snap              # List snap jobs
GET    /seller/snap/{id}         # Get snap job details
DELETE /seller/snap/{id}         # Delete draft
POST   /seller/snap/{id}/publish # Publish to marketplaces

# Inventory
GET    /my-items                 # List seller's items
POST   /my-items                 # Create item manually
PUT    /my-items/{id}            # Update item
DELETE /my-items/{id}            # Delete item

# Cross-posts
GET    /seller/cross-posts       # List all cross-posts
GET    /seller/cross-posts/{id}  # Get cross-post status

# Pricing
POST   /seller/pricing/suggest   # Get price suggestions

# Marketplace Accounts
GET    /marketplace-accounts     # List connected accounts
POST   /marketplace-accounts     # Add account manually
DELETE /marketplace-accounts/{id} # Disconnect account

# OAuth Flows
GET    /ebay/authorize           # Start eBay OAuth
POST   /ebay/exchange            # Exchange code for token
GET    /facebook-oauth/authorize # Start Facebook OAuth
POST   /facebook-oauth/callback  # Handle callback
GET    /offerup-oauth/authorize  # Start OfferUp OAuth
POST   /offerup-oauth/callback   # Handle callback
```

### Health & Monitoring

```bash
GET /health                      # Service health check
GET /ping                        # Simple connectivity test
GET /metrics                     # Prometheus metrics
```

## 🔄 Celery Tasks

### Active (Seller-Focused)

- **`process_snap.process_snap_job`**: Process uploaded photos with AI vision
- **`refresh_comps.refresh_comps_task`**: Update pricing data (nightly at 3 AM)
- **`reconcile_sales.reconcile_sales_task`**: Sync marketplace sales (hourly)

### Parked (Buyer-Focused)

- `scan_all.run_scan_all` - Marketplace scanning (disabled)
- `notify.send_notifications` - Buyer notifications (disabled)
- `check_all_deal_alerts` - Alert monitoring (disabled)

## 🧪 Development

### Run Locally (without Docker)

**Backend:**
```bash
cd backend
pip install -e .
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Worker:**
```bash
cd backend
celery -A app.worker worker --loglevel=info
```

**Beat (scheduler):**
```bash
cd backend
celery -A app.worker beat --loglevel=info
```

### Database Migrations

```bash
# Create migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📋 Environment Variables

### Required

- `DATABASE_URL` - Postgres connection string
- `REDIS_URL` - Redis connection string

### Optional but Recommended

- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` - For AI vision
- `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET` - For image hosting
- `EBAY_APP_ID`, `EBAY_CERT_ID`, `EBAY_DEV_ID` - For eBay integration
- `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET` - For Facebook integration
- `OFFERUP_CLIENT_ID`, `OFFERUP_CLIENT_SECRET` - For OfferUp integration

See `.env.example` for complete list.

## 🚢 Deployment

See [DEPLOY.md](./DEPLOY.md) for production deployment guide (Render + Vercel).

## 📚 Documentation

- **Architecture**: See `/docs/ARCHITECTURE.md`
- **API Reference**: http://localhost:8000/docs (when running)
- **Archived Features**: `/archive/README.md`
- **Deployment**: `DEPLOY.md`

## 🤝 Contributing

1. Create feature branch from `main`
2. Make changes
3. Run tests (`pytest`, `npm test`)
4. Submit PR with clear description

## 📄 License

[Add your license here]

## 🆘 Support

- **Issues**: GitHub Issues
- **Docs**: `/docs` directory
- **API Docs**: http://localhost:8000/docs

---

**Built with**: FastAPI • Next.js • Celery • Redis • Postgres • Claude AI • Docker
