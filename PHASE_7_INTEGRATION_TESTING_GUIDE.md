# 🧪 Phase 7 Integration Testing Guide

**Purpose:** End-to-end testing of the complete Phase 7 deal alert system

**Scope:** Creating rules → Testing matches → Receiving notifications

---

## ✅ Pre-Test Checklist

Before starting, ensure:

- [ ] Backend running: `docker compose up -d --build backend`
- [ ] Frontend running: `npm run dev` in `frontend/` directory
- [ ] PostgreSQL database accessible
- [ ] Redis cache accessible
- [ ] Celery worker running (optional, but recommended)
- [ ] Gmail SMTP configured (for email notifications)
- [ ] Discord webhook URL ready (for Discord testing)

---

## 🚀 Test Scenario 1: Create & Test a Deal Alert Rule

### Step 1: Navigate to Deal Alerts Dashboard

```
1. Open browser to http://localhost:3002/buyer/alerts
2. Should see empty dashboard or existing rules
3. Click "New Alert Rule" button
```

### Step 2: Create a Test Rule

```
Fill the form with:
- Name: "Test Gaming Laptops Under $1000"
- Keywords: gaming, laptop, RTX
- Exclude Keywords: broken, damaged
- Max Price: 1000
- Categories: Electronics, Computers
- Minimum Condition: good
- Notification Channels: Email ✓

Click "Create Alert Rule"
```

### Expected Result:

```
✅ Rule saved successfully
✅ Modal closes
✅ Status message: "Deal alert rule created successfully!"
✅ New rule appears in dashboard with:
   - Name displayed
   - Status: "Active" (green badge)
   - Keywords shown
   - Price range displayed
   - Categories listed
   - Email channel icon
   - Test button enabled
```

---

## 🧪 Test Scenario 2: Test Rule Matching

### Step 3: Test the Rule

```
1. On the rule card, click "Test Rule" button
2. Button changes to "Testing..."
3. Wait for modal to appear with results
```

### Expected Result:

```
✅ Modal shows "Test Results (X matches)"
✅ Each match displays:
   - Thumbnail image
   - Title
   - Price (green)
   - Condition
   - Deal score
   - "View Listing" link

If matching listings exist in database:
✅ Shows 1-100 listings matching the rule criteria

If no matches found:
✅ Shows "No listings match this rule" message
```

### Step 4: Review Test Results

```
1. Examine the matches
2. Verify they meet the rule criteria:
   - Contains keyword (gaming OR laptop OR RTX)
   - Does NOT contain (broken OR damaged)
   - Price ≤ $1000
   - Category is Electronics or Computers
   - Condition ≥ good
3. Close modal by clicking "Close"
```

---

## 🔔 Test Scenario 3: Configure Notifications

### Step 5: Navigate to Notification Preferences

```
1. Click on /buyer/preferences in header OR
2. Navigate directly to http://localhost:3002/buyer/preferences
3. Should see Notification Preferences page
```

### Expected Result:

```
✅ Page loads with sections:
   - Notification Channels (checkboxes)
   - Discord Webhook Configuration (if Discord selected)
   - Notification Frequency (Immediate/Daily/Weekly)
   - Quiet Hours (toggle + time inputs)
   - Rate Limiting (max per day)
   - Tips section
```

### Step 6: Enable Email Channel

```
1. Verify "email" checkbox is checked
2. If not, click to enable
3. Status message should appear: "Channels updated successfully"
```

### Expected Result:

```
✅ Email channel enabled
✅ Status message appears and disappears after 3 seconds
```

### Step 7: Configure Discord Webhook

```
1. Check "discord" checkbox
2. Status: "Channels updated successfully"
3. Discord section appears below
4. Click "Add Discord Webhook"
5. Enter your Discord webhook URL
6. Click "Add Webhook"
```

### Expected Result:

```
✅ Webhook input appears
✅ After submission:
   - Green confirmation message
   - "Discord webhook configured" message
   - Test Webhook button appears
   - Remove Webhook button appears
```

### Step 8: Test Discord Webhook

```
1. On Discord Webhook Configuration, click "Test Webhook"
2. Check your Discord server/channel
```

### Expected Result:

```
✅ Status message: "Test message sent to Discord!"
✅ Discord channel receives test message:
   {
     "embeds": [{
       "title": "Discord Webhook Test",
       "description": "This is a test message from Deal Scout",
       "color": 0x00FF00
     }]
   }
```

### Step 9: Configure Quiet Hours

```
1. Check "Enable quiet hours" checkbox
2. Set Start Time: 22:00 (10 PM)
3. Set End Time: 08:00 (8 AM)
4. Click "Save Quiet Hours"
```

### Expected Result:

```
✅ Status message: "Quiet hours updated successfully!"
✅ Quiet hours configuration saved
✅ No notifications sent between 10 PM - 8 AM
```

### Step 10: Configure Notification Frequency

```
1. Select "Daily Digest" from Delivery Mode dropdown
2. Set Digest Time to 09:00
3. Click "Save Frequency Settings"
```

### Expected Result:

```
✅ Status message: "Frequency updated successfully!"
✅ Notifications now delivered once daily at 9 AM
   (instead of immediately on each match)
```

---

## 🔄 Test Scenario 4: Background Task Execution

### Step 11: Wait for Background Task

The Celery beat scheduler runs automatically:

```
Background task: check_all_deal_alerts
Schedule: Every 30 minutes
Time for next run: <wait up to 30 minutes OR manually trigger>
```

### Manual Trigger (via API):

```bash
# If you have access to Celery/Redis, trigger manually:
curl -X POST http://localhost:8000/tasks/run/check_all_deal_alerts \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### Expected Result (Backend Logs):

```
Checking 1 enabled deal alert rules
Rule 1 (Test Gaming Laptops Under $1000): Found 5 matches
Sending email to user@example.com
Email sent to user@example.com for listing 12345
Discord notification sent for listing 12345
Rule last_triggered_at updated to 2025-10-31T12:34:56Z
```

---

## 📧 Test Scenario 5: Receive Email Notification

### Step 12: Check Email Inbox

If email is configured (SMTP settings in .env):

```
From: Deal Scout <alerts@dealscout.local>
To: <your-email@example.com>
Subject: Deal Alert: Test Gaming Laptops Under $1000

Body contains:
- Deal Alert title
- Listing title
- Price: $XXX.XX
- Category: Electronics
- Condition: Good
- Location (if available)
- [View Listing on Facebook] or [View Listing on Offerup] links
```

### Expected Result:

```
✅ Email received with:
   - Correct alert rule name
   - Matching listing details
   - Correct price
   - Working links to marketplace listings
   - Professional HTML formatting
```

### Step 13: Check Discord Notification

If Discord webhook is configured:

```
Discord message embeds:
- Title: "Deal Alert: Test Gaming Laptops Under $1000"
- Description: Listing title
- Color: Green (0x00FF00)
- Fields:
  - Price: $XXX.XX
  - Category: Electronics
  - Condition: Good
  - Link: [View Listing](url)
- Thumbnail: Product image
```

### Expected Result:

```
✅ Discord message received with:
   - Correct alert name
   - Listing details
   - Embedded image
   - Clickable link
```

---

## 🎯 Test Scenario 6: Rule Management

### Step 14: Pause a Rule

```
1. Go to /buyer/alerts dashboard
2. Click "Pause" button on a rule
```

### Expected Result:

```
✅ Rule status changes from "Active" to "Paused"
✅ Rule badge changes from green to gray
✅ Background task will NOT check this rule anymore
```

### Step 15: Resume a Rule

```
1. Click "Resume" button on paused rule
```

### Expected Result:

```
✅ Rule status changes from "Paused" to "Active"
✅ Rule badge changes from gray to green
✅ Background task will check this rule again
```

### Step 16: Delete a Rule

```
1. Click "Delete" button on a rule
2. Confirm deletion in browser popup
```

### Expected Result:

```
✅ Confirmation dialog appears
✅ Rule removed from dashboard
✅ Database record deleted
✅ No further notifications sent
```

---

## 📊 Test Scenario 7: Advanced Rules

### Step 17: Create Rule with Location Filter

```
Create rule with:
- Name: "Furniture Near Me"
- Keywords: furniture
- Location: San Jose, CA
- Radius: 50 miles
- Max Price: 500
- Channels: Email ✓

Click "Create Alert Rule"
```

### Expected Result:

```
✅ Rule created successfully
✅ Rule card shows:
   - Location: San Jose, CA (50 mi radius)
   - Price range: $0 - $500
✅ Test rule returns only furniture within 50 miles
```

### Step 18: Create Rule with Deal Score

```
Create rule with:
- Name: "Hot Deals Only"
- Keywords: gaming
- Min Deal Score: 0.75
- Channels: Email ✓

Click "Create Alert Rule"
```

### Expected Result:

```
✅ Rule created successfully
✅ Rule card shows:
   - Min Deal Score: 0.75
✅ Test rule returns only deals with score ≥ 0.75
```

---

## 🚨 Error Handling Tests

### Step 19: Test Missing Required Field

```
1. Click "New Alert Rule"
2. Leave Name empty
3. Click "Create Alert Rule"
```

### Expected Result:

```
✅ Error message: "Rule name is required"
✅ Form does not submit
✅ Modal stays open
```

### Step 20: Test Invalid Discord Webhook

```
1. Go to /buyer/preferences
2. Enable Discord
3. Enter invalid URL: "not-a-real-url"
4. Click "Add Webhook"
```

### Expected Result:

```
✅ Error message: "Failed to add Discord webhook"
✅ Form stays open
✅ User can retry with correct URL
```

### Step 21: Test Server Error Handling

```
1. Stop backend: docker compose down backend
2. Try to create a rule
3. Start backend again
```

### Expected Result:

```
✅ Error message appears: "Failed to create deal alert rule"
✅ User can retry when service is back up
✅ No corrupted data in database
```

---

## 📈 Performance Tests

### Step 22: Test with Many Rules

```
1. Create 10 deal alert rules through UI
2. Dashboard should handle loading
3. Click through pagination if needed
```

### Expected Result:

```
✅ All 10 rules load within 2 seconds
✅ SWR caching prevents unnecessary refetches
✅ Auto-refresh every 30 seconds works smoothly
```

### Step 23: Test Rule Testing Performance

```
1. Test a rule that returns 100 matches
2. Modal should load in < 2 seconds
```

### Expected Result:

```
✅ Test results modal appears quickly
✅ All 100 matches rendered smoothly
✅ No browser freezing
```

---

## 🔐 Security Tests

### Step 24: Test Authentication

```
1. Open browser console (F12)
2. Clear localStorage: localStorage.clear()
3. Try to navigate to /buyer/alerts
```

### Expected Result:

```
✅ Redirected to login page
✅ Cannot access protected pages without JWT token
```

### Step 25: Test Unauthorized Access

```
1. Create valid JWT token for User A
2. Modify token to claim User B's ID
3. Try to create/modify/delete User A's rules
```

### Expected Result:

```
✅ Backend rejects the request
✅ 401 Unauthorized error
✅ User cannot access other user's rules
```

---

## 📋 Comprehensive Test Checklist

### Dashboard Tests:
- [ ] Dashboard loads without errors
- [ ] Statistics cards show correct counts
- [ ] Rules list refreshes automatically
- [ ] Empty state shows when no rules exist
- [ ] Status messages appear and disappear

### Create Rule Tests:
- [ ] Modal opens and closes correctly
- [ ] Form validation works
- [ ] Required fields are enforced
- [ ] Keywords split correctly on comma
- [ ] Category multi-select works
- [ ] Price range validation works
- [ ] Submit success shows status message

### Test Rule Tests:
- [ ] Test button becomes disabled while loading
- [ ] Test results modal appears
- [ ] Matching listings display correctly
- [ ] No matches shows appropriate message
- [ ] Modal closes on close button click

### Notification Preference Tests:
- [ ] Channels can be toggled
- [ ] Discord webhook can be added/removed
- [ ] Discord webhook can be tested
- [ ] Quiet hours can be configured
- [ ] Frequency can be changed
- [ ] Max per day can be set
- [ ] Status messages confirm changes

### Background Task Tests:
- [ ] Task runs every 30 minutes
- [ ] Email notifications are sent
- [ ] Discord notifications are sent
- [ ] Quiet hours are respected
- [ ] Rate limiting works
- [ ] last_triggered_at is updated

### Error Tests:
- [ ] Missing required fields show error
- [ ] Invalid Discord URL shows error
- [ ] Network errors are handled gracefully
- [ ] Server errors show user-friendly messages

---

## 🎬 Complete End-to-End Test Script

```bash
# 1. Start all services
docker compose up -d --build backend
npm run dev  # in frontend directory

# 2. Wait for services to be ready
sleep 5

# 3. Login to get JWT token (manual step in browser)
# Navigate to login page, enter credentials

# 4. Create a deal alert rule (manual step in UI)
# Go to /buyer/alerts
# Click "New Alert Rule"
# Create: "Test Rule - Gaming Under $800"

# 5. Test the rule (manual step in UI)
# Click "Test Rule" button
# Verify matches appear

# 6. Configure notifications (manual step in UI)
# Go to /buyer/preferences
# Enable Email and Discord
# Add Discord webhook
# Click "Test Webhook"

# 7. Set quiet hours (manual step in UI)
# Enable quiet hours
# Set 10 PM - 8 AM

# 8. Wait for background task (or trigger manually)
# Monitor backend logs for "Checking N enabled deal alert rules"
# Should see "Rule X: Found Y matches"

# 9. Check email and Discord for notifications
# Verify format and content

# 10. Manage rules (manual step in UI)
# Try pause/resume/delete
# Verify each action works

echo "✅ All integration tests complete!"
```

---

## 🐛 Troubleshooting

### Issue: Rules not showing on dashboard

```
1. Check JWT token is valid
2. Verify user is authenticated
3. Check database has rules for this user
4. Look at browser console for errors
5. Check backend logs for API errors
```

### Issue: Test rule returns no matches

```
1. Verify listings exist in database
2. Check rule criteria are reasonable
3. Review listing data in database
4. Manually test rule criteria in SQL
5. Check that keywords match listing titles/descriptions
```

### Issue: Email not received

```
1. Check SMTP settings in .env
2. Look at backend email logs
3. Check spam folder
4. Verify email address in user profile
5. Test email sending manually
```

### Issue: Discord webhook not working

```
1. Verify webhook URL is correct
2. Check Discord permission settings
3. Test webhook with curl:
   curl -X POST <webhook_url> \
     -H "Content-Type: application/json" \
     -d '{"content":"test"}'
4. Check webhook has been deleted
5. Create new webhook URL
```

### Issue: Background task not running

```
1. Verify Celery worker is running
2. Check Redis connection
3. Look at Celery logs for errors
4. Manually trigger task via API
5. Check task schedule in worker.py
```

---

## ✨ Success Criteria

Phase 7 is considered complete when:

✅ User can create deal alert rules via UI
✅ Rules appear in dashboard immediately
✅ Test rule shows matching listings
✅ User can configure notification preferences
✅ Email notifications are received
✅ Discord notifications are received
✅ Background task runs every 30 minutes
✅ Rules are checked and matches found
✅ Notifications respect quiet hours
✅ User can pause/resume/delete rules
✅ No authentication bypasses
✅ Error messages are helpful
✅ System handles edge cases
✅ Performance is acceptable
✅ Mobile design is responsive

---

**Phase 7 Integration Testing Guide - Ready to Test ✅**

Date: October 31, 2025
Purpose: Complete system validation
Impact: End-to-end user experience verification

