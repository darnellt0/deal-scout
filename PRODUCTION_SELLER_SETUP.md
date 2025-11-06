# 🚀 Production Seller Setup Guide
**Goal:** Walk into storage, take photos, list on eBay/marketplaces, make sales
**Timeline:** 1-2 hours to full production readiness
**Users:** You and your wife

---

## 📋 What You're Building

**Your Complete Workflow:**
```
Storage Area → Take Photos → Upload to Deal Scout → AI Processes →
Review/Edit → One-Click Post to eBay → Manage Sales → Profit
```

**What the System Does for You:**
1. ✅ Detects item category from photos (AI vision)
2. ✅ Suggests condition (excellent/good/fair)
3. ✅ Writes compelling title and description (AI copywriter)
4. ✅ Suggests competitive price (using eBay sold comparables)
5. ✅ Cleans and optimizes images (background removal optional)
6. ✅ Posts to eBay (one-click when ready)
7. ✅ Tracks all your listings in one dashboard

---

## 🎯 Phase 1: Get API Keys (30 minutes)

### 1. OpenAI API Key (Required for AI Features)

**Why you need it:**
- AI vision to detect items from photos
- Auto-generate listing titles and descriptions
- Condition assessment

**How to get it:**
1. Go to https://platform.openai.com/signup
2. Create account (or sign in)
3. Go to https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Name it: "Deal Scout Production"
6. Copy the key (starts with `sk-...`)
7. **Save it somewhere safe** (you can't see it again!)

**Cost estimate:**
- Vision API: ~$0.01-0.03 per photo
- Text generation: ~$0.001 per listing
- **Expected cost:** $5-20/month for moderate use

### 2. eBay Developer Account (Required for Listings)

**Why you need it:**
- List items to eBay automatically
- Get price comparables
- Manage your inventory

**How to get it:**

**Step 1: Create eBay Developer Account**
1. Go to https://developer.ebay.com/
2. Click "Join" or "Sign In"
3. Create account using your selling eBay account
4. Accept developer program terms

**Step 2: Create Production Application**
1. Go to https://developer.ebay.com/my/keys
2. Click "Create Application Keys"
3. Choose **Production** (not Sandbox!)
4. Fill in details:
   - Application Title: "Deal Scout Seller"
   - Short Description: "Personal marketplace listing tool"
   - Privacy Policy URL: `http://localhost:8000/privacy` (or leave blank for personal use)

**Step 3: Get Your Keys**
You'll receive three keys:
- **App ID** (Client ID)
- **Dev ID**
- **Cert ID** (Client Secret)

**Save all three!**

**Step 4: Grant Token**
You need a User Token to actually post listings:
1. In your eBay dev dashboard, find your app
2. Click "User Tokens"
3. Click "Get a Token from eBay via Your Application"
4. Select scopes:
   - `https://api.ebay.com/oauth/api_scope/sell.inventory`
   - `https://api.ebay.com/oauth/api_scope/sell.account`
   - `https://api.ebay.com/oauth/api_scope/sell.marketing`
   - `https://api.ebay.com/oauth/api_scope/sell.fulfillment`
5. Click "Sign in to Production"
6. Sign in with your eBay seller account
7. Grant access
8. Copy the **OAuth User Token** (starts with `v^1.1#...`)

**Important:** eBay tokens expire every ~2 hours. Deal Scout will handle refresh automatically once you do the initial OAuth flow.

### 3. Optional: AWS S3 for Image Storage

**Why you might want it:**
- Persistent image storage (doesn't disappear if you restart Docker)
- CDN delivery for faster loading
- Professional image URLs

**How to set it up:**
1. Go to https://aws.amazon.com/s3/
2. Create AWS account (free tier available)
3. Create S3 bucket:
   - Name: `dealscout-images-yourname`
   - Region: US West (Oregon) or your preferred
   - Uncheck "Block all public access" (images need to be public)
4. Create IAM user for access:
   - Go to IAM → Users → Create User
   - Name: `dealscout-s3-access`
   - Attach policy: `AmazonS3FullAccess` (or create custom policy)
   - Create access key
   - Save **Access Key ID** and **Secret Access Key**

**Cost:** ~$1-5/month for hundreds of images

---

## 🔧 Phase 2: Configure Your Environment (15 minutes)

### Update Your `.env` File

Open `/home/user/deal-scout/.env` and update these values:

```bash
# ============================================================================
# PRODUCTION CONFIGURATION
# ============================================================================

# Switch to production mode
DEMO_MODE=false

# OpenAI API (paste your key here)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
VISION_ENABLED=true
REMBG_ENABLED=true  # Set to false if you want to keep backgrounds

# eBay Production Configuration
EBAY_ENV=production  # Changed from 'sandbox'
EBAY_APP_ID=YourAppI-DealScou-PRD-xxxxxxxxxxxxx
EBAY_CERT_ID=PRD-xxxxxxxxxxxxx-xxxxxxxx
EBAY_DEV_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
EBAY_OAUTH_TOKEN=v^1.1#i^1#xxxxx...  # Your user token
EBAY_REFRESH_TOKEN=  # Leave empty initially, will auto-populate
EBAY_REDIRECT_URI=urn:ietf:wg:oauth:2.0:oob
EBAY_MARKETPLACE_ID=EBAY_US

# Price Suggestions
PRICE_SUGGESTION_MODE=ebay_only  # Use real eBay sold listings

# Optional: AWS S3 for image storage
# Leave empty to use local storage (backend/static/)
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=dealscout-images-yourname
S3_IMAGE_PREFIX=images/

# Email notifications (optional - for sale notifications)
# Use your real SMTP for production
EMAIL_FROM=your-email@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password  # Use app password, not regular password

# Your location for local marketplace scanning
DEFAULT_CITY="Your City, State"
DEFAULT_RADIUS_MI=50
```

**Important Security Notes:**
- Never commit your `.env` file to git
- Keep your API keys private
- Use app passwords for Gmail (not your regular password)

---

## 🐳 Phase 3: Start Production System (10 minutes)

### 1. Start All Services

```bash
cd /home/user/deal-scout

# Stop any existing containers
docker compose down

# Build and start fresh
docker compose up -d --build

# Wait ~60 seconds for everything to start

# Check status
docker compose ps
```

**Expected output:**
```
NAME                          STATUS
deal-scout-backend-1          Up (healthy)
deal-scout-worker-1           Up
deal-scout-beat-1             Up
deal-scout-frontend-1         Up
deal-scout-postgres-1         Up (healthy)
deal-scout-redis-1            Up (healthy)
```

### 2. Verify System Health

```bash
# Check backend API
curl http://localhost:8000/health

# Should return:
# {"ok":true,"db":true,"redis":true,"queue_depth":0,"version":"0.1.0"}
```

### 3. Access the System

Open in your browser:
- **Frontend:** http://localhost:3000
- **Seller Dashboard:** http://localhost:3000/seller
- **API Docs:** http://localhost:8000/docs

### 4. Create Image Storage Directory

```bash
# Create local image storage (if not using S3)
mkdir -p backend/static/uploads
mkdir -p backend/static/processed
chmod -R 777 backend/static/  # Allow uploads
```

---

## 👥 Phase 4: Create User Accounts (10 minutes)

### Create Accounts for You and Your Wife

**Option 1: Via Frontend (Recommended)**
1. Go to http://localhost:3000
2. Click "Sign Up"
3. Fill in:
   - Username: `yourname`
   - Email: `your-email@gmail.com`
   - Password: (choose strong password)
   - Role: Select "Seller" ✅
4. Click "Create Account"
5. Login
6. Repeat for your wife's account

**Option 2: Via API (Direct)**
```bash
# Create your account
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "yourname",
    "email": "your-email@gmail.com",
    "password": "YourStrongPassword123",
    "role": "seller"
  }'

# Create your wife's account
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "wifename",
    "email": "wife-email@gmail.com",
    "password": "HerStrongPassword123",
    "role": "seller"
  }'
```

**Save the tokens returned!** You'll use these to authenticate API calls.

---

## 📸 Phase 5: Test the Complete Workflow (20 minutes)

### The Full Seller Journey - Let's Test It!

**Step 1: Login**
1. Go to http://localhost:3000
2. Login with your credentials
3. Navigate to http://localhost:3000/seller

**Step 2: Upload Your First Test Photo**

For testing, use any item you have nearby:
1. Take photo with your phone
2. Transfer to computer
3. In Deal Scout, click "Upload Photos" or drag and drop
4. Wait for processing (~10-30 seconds)

**Step 3: What Happens Automatically**

The system will:
1. ✅ Detect the item (e.g., "gaming chair", "vintage lamp", "kitchen table")
2. ✅ Assess condition (excellent/good/fair based on image quality)
3. ✅ Generate listing title (e.g., "Vintage Mid-Century Table Lamp - Excellent Condition")
4. ✅ Write description with selling points
5. ✅ Search eBay for comparable sold listings
6. ✅ Suggest competitive price (e.g., "Similar items sold for $45-$65, suggest $55")
7. ✅ Clean/optimize images (optional background removal)

**Step 4: Review and Edit**

You'll see a draft listing:
```
Title: Vintage Mid-Century Table Lamp - Excellent Condition
Price: $55.00 (suggested)
Condition: Excellent
Category: Home & Garden > Lamps

Description:
Beautiful vintage mid-century modern table lamp in excellent working
condition. Features brass base and geometric shade. Perfect for adding
retro charm to any room. All original parts, no damage.

Comparable Sales:
- Similar lamp sold for $62 (3 days ago)
- Similar lamp sold for $48 (1 week ago)
- Average: $55

Images: [3 photos - cleaned and optimized]
```

**Step 5: Make Any Edits**
- Adjust price if you want
- Edit title/description
- Change condition
- Add more details

**Step 6: Post to eBay**

Click "Post to eBay" button:
1. System creates eBay listing via API
2. Images uploaded to eBay
3. Listing goes live on eBay immediately
4. Returns eBay item ID and URL
5. Saves to your "My Items" dashboard

**Step 7: Track Your Listing**

Go to "My Items" dashboard to see:
- All your active listings
- Views and watchers (synced from eBay)
- Messages from buyers
- Sale status

---

## 📱 Phase 6: Daily Seller Workflow (Your Production Process)

### Every Day in Storage:

**Morning Setup (2 minutes):**
```bash
# 1. Make sure system is running
docker compose ps

# 2. Open Deal Scout
# Browser: http://localhost:3000/seller

# 3. Login
```

**For Each Item (5-10 minutes per item):**

1. **Find Item in Storage**
   - Pick an item to sell

2. **Take Photos (1-2 minutes)**
   - Take 3-5 photos:
     - Front view
     - Side/back view
     - Close-up of details
     - Close-up of any flaws (be honest!)
     - Item in use (if applicable)
   - Tips:
     - Good lighting (natural light is best)
     - Plain background if possible
     - Show scale (put something next to it)
     - Clear, focused shots

3. **Upload to Deal Scout (30 seconds)**
   - Drag and drop photos
   - Click "Process"

4. **Wait for AI (30 seconds)**
   - System processes images
   - Generates listing draft

5. **Review and Edit (2-3 minutes)**
   - Check AI-generated title - tweak if needed
   - Review description - add specifics AI can't see:
     - Brand name (if not visible)
     - Measurements (AI can estimate, but measure to be sure)
     - Any history ("bought new in 2020", "rarely used")
     - Why you're selling (optional)
   - Verify price suggestion:
     - Check comparable sales shown
     - Adjust based on your item's condition
     - Consider your desired timeline (price higher for patience, lower for quick sale)

6. **Post to eBay (10 seconds)**
   - Click "Post to eBay"
   - Wait for confirmation
   - Listing is live!

7. **Physical Organization (1-2 minutes)**
   - Label item with eBay item # (sticker or tag)
   - Place in "listed items" area of storage
   - Note location in your system if needed

**Daily Totals:**
- 5 items/hour realistic pace
- 20-30 items/day if you're focused
- 100+ items/week possible

### Tips for Maximum Efficiency

**Photography Station:**
- Set up dedicated photo area in storage
- Good overhead lighting
- White poster board for backdrop ($5 at Target)
- Phone tripod ($15 on Amazon)
- Batch photos: take pics of 5-10 items, then upload all at once

**Categories to Start With (Easiest to Sell):**
1. Electronics (high value, popular)
2. Furniture (local pickup, no shipping hassle)
3. Brand-name clothing
4. Kitchen appliances
5. Tools
6. Sports equipment
7. Collectibles (if you know values)

**Avoid These (Hard to Sell):**
- Unknown brands
- Heavy items requiring freight shipping
- Heavily used clothing
- Incomplete sets
- Items worth <$10 (not worth the time)

---

## 🎯 Phase 7: Managing Sales and Buyers

### When You Get a Sale

**1. Deal Scout Notifications:**
- Email notification: "Item #123456 sold!"
- Dashboard shows "SOLD" status
- Buyer info and shipping address shown

**2. Your Action Steps:**
1. Print shipping label (from eBay)
2. Find item in storage (using your item # tag)
3. Pack item securely
4. Ship within 1-2 business days (for good seller rating)
5. Mark as shipped in eBay
6. Deal Scout auto-syncs sale status

**3. Buyer Messages:**
- Messages from eBay show in Deal Scout dashboard
- Reply directly from Deal Scout or eBay
- Common questions:
  - "What are dimensions?" (add measurements to future listings!)
  - "Can you ship faster?" (offer upgrade if possible)
  - "Is this still available?" (yes, if listing is active)

### Handling Returns

If buyer requests return:
1. Be polite and professional
2. Accept return if eBay policy requires it
3. Issue refund when item is received
4. Relist item (photos/description already in Deal Scout!)

---

## 💰 Pricing Strategy

### AI Price Suggestions vs. Your Knowledge

**AI is good at:**
- Finding comparable sold listings
- Calculating average market price
- Identifying price trends

**You know better:**
- Actual condition (AI can't see scratches on underside)
- Completeness (missing parts, accessories)
- Brand reputation in your niche
- Your cost basis (what you paid)
- How fast you need to sell

**Recommended Approach:**
1. Start with AI suggestion
2. Adjust up if:
   - Excellent condition
   - Rare/hard to find
   - Complete with all accessories
   - Original packaging
3. Adjust down if:
   - Minor flaws
   - Missing accessories
   - Common item
   - Want quick sale

**Pricing Tiers:**
- **Premium (AI price + 20%):** Rare items, excellent condition, patient
- **Market (AI price):** Average condition, normal timeline
- **Quick Sale (AI price - 20%):** Good condition, need cash fast
- **Clearance (AI price - 40%):** Fair condition, taking up space

### Example Pricing Decision

**AI Suggests:** $55 for vintage lamp
**Your Analysis:**
- Lamp has small chip on base (not visible in photos) = -$10
- You have original box = +$5
- You paid $20 at estate sale = ok to sell at $40-50
- **Your Price:** $48 (quick sale, still profitable)

---

## 📊 Tracking Your Business

### Weekly Review (30 minutes)

Check your dashboard:

**Metrics to Track:**
```
Week of [Date]:
- Items listed: 25
- Items sold: 8
- Total revenue: $487
- Average sale price: $60.88
- Time invested: ~10 hours
- Hourly rate: $48.70

Categories performing best:
1. Electronics: 4 sales, avg $78
2. Furniture: 3 sales, avg $52
3. Kitchen: 1 sale, $35

Top selling items:
- Vintage radio: $125
- Gaming chair: $89
- Coffee maker: $35
```

**Adjust Strategy:**
- List more of what's selling
- Lower prices on items sitting >2 weeks
- Take better photos if views are low
- Add more detail if watchers aren't buying

---

## 🐛 Troubleshooting Common Issues

### Issue: "Upload failed"
**Causes:**
- Image too large (>10MB)
- Network issue
- Backend not running

**Fix:**
```bash
# Check if backend is running
docker compose ps backend

# Restart if needed
docker compose restart backend

# Check logs
docker compose logs backend --tail=50
```

### Issue: "AI detection failed"
**Causes:**
- No OpenAI API key
- Invalid API key
- Out of API credits

**Fix:**
1. Check `.env` file has `OPENAI_API_KEY=sk-...`
2. Verify key at https://platform.openai.com/api-keys
3. Check usage/credits: https://platform.openai.com/usage

### Issue: "Can't post to eBay"
**Causes:**
- Invalid eBay credentials
- Expired OAuth token
- Missing required fields

**Fix:**
1. Check eBay token hasn't expired
2. Re-run OAuth flow if needed
3. Verify all required fields filled:
   - Title (required)
   - Price (required)
   - Category (required)
   - At least 1 photo (required)

### Issue: "Price suggestions not showing"
**Causes:**
- No eBay API access
- Item category not found
- No comparable sales

**Fix:**
1. Check `PRICE_SUGGESTION_MODE=ebay_only` in `.env`
2. Verify eBay API credentials
3. Try broader category
4. Manually set price if needed

### Issue: "Images not displaying"
**Causes:**
- Image path wrong
- Permissions issue
- S3 bucket not configured

**Fix (Local Storage):**
```bash
# Check directory exists
ls -la backend/static/

# Fix permissions
chmod -R 777 backend/static/

# Create if missing
mkdir -p backend/static/uploads
mkdir -p backend/static/processed
```

**Fix (S3):**
1. Check S3 bucket is public
2. Verify AWS credentials in `.env`
3. Test upload manually

---

## 🚀 Going Further

### Multi-Marketplace Expansion

**Currently Supported:**
- ✅ eBay (full integration)
- 🚧 Facebook Marketplace (prepared, needs OAuth)
- 🚧 OfferUp (prepared, needs OAuth)
- 🚧 Craigslist (prepared, needs implementation)

**Future Sessions:**
We can add:
- Facebook Marketplace auto-posting
- OfferUp integration
- Poshmark (for clothing)
- Mercari
- Local pickup coordination

### Advanced Features to Enable

**Bulk Operations:**
- Upload 10 photos → auto-detect as 10 items
- Batch pricing
- Scheduled posting (list 5 items/day automatically)

**Analytics Dashboard:**
- Revenue tracking
- Best selling categories
- Time to sale metrics
- ROI per item

**Automation:**
- Auto-relist unsold items after 30 days
- Auto price drops for items >14 days old
- Auto-send thank you messages
- Feedback automation

---

## ✅ Success Checklist

Before you start selling, verify:

**System Setup:**
- [ ] Docker services all running (`docker compose ps`)
- [ ] Backend health check passes (`curl localhost:8000/health`)
- [ ] Frontend loads (http://localhost:3000)
- [ ] OpenAI API key configured
- [ ] eBay production credentials set
- [ ] Image storage working (local or S3)

**User Accounts:**
- [ ] Your account created and can login
- [ ] Wife's account created and can login
- [ ] Both accounts have "seller" role

**First Test Listing:**
- [ ] Uploaded photo successfully
- [ ] AI detected item correctly
- [ ] Got price suggestion from eBay
- [ ] Title and description generated
- [ ] Can edit listing details
- [ ] Successfully posted to eBay (or saved draft)

**Physical Setup:**
- [ ] Photography area set up
- [ ] Good lighting available
- [ ] Labels/tags for item tracking
- [ ] Shipping supplies on hand
- [ ] Packing materials ready

---

## 📞 Next Steps

**You're ready to start selling when:**
1. All checkboxes above are ✅
2. You've done 1 successful test listing
3. System is running smoothly
4. You understand the workflow

**First Week Goals:**
- List 10-20 items
- Make 2-3 sales
- Get comfortable with workflow
- Identify any friction points

**We Can Optimize:**
- Batch processing for faster listing
- Better photography templates
- Category-specific templates
- Automated repricing
- Multi-marketplace posting

---

## 🎓 Resources

**Deal Scout Documentation:**
- `PHASE_7_QUICK_START.md` - System overview
- `TESTING_CHEAT_SHEET.md` - API testing
- `QUICK_REFERENCE.md` - Command reference

**External Resources:**
- eBay Seller Hub: https://www.ebay.com/sh/ovw
- eBay Fee Calculator: https://www.fees.ebay.com/feeweb/feeillustrator
- OpenAI Usage: https://platform.openai.com/usage
- Photography Tips: YouTube "eBay product photography"

**Support:**
- Check logs: `docker compose logs -f backend`
- API docs: http://localhost:8000/docs
- System health: http://localhost:8000/health

---

## 💡 Pro Tips from Experienced Sellers

1. **Take photos in batches** - Process 10 items at once, more efficient
2. **Measure everything** - Buyers always ask for dimensions
3. **Be honest about condition** - Saves returns and bad feedback
4. **Ship fast** - Good seller rating = more sales
5. **Keep it simple** - List items, ship items, repeat
6. **Start small** - 5-10 listings to learn, then scale up
7. **Track your time** - Know your hourly rate, stop if not profitable
8. **Seasonal timing** - Some items sell better certain times of year
9. **Bundle accessories** - "Complete set" sells better than parts
10. **Price to sell** - Better to sell at $40 today than $50 never

---

**You're Ready! 🎉**

Walk into that storage area with confidence. Deal Scout has your back from photo to sale.

**Questions or issues?** We can troubleshoot and optimize as you go.

**Let's make some sales! 💰**
