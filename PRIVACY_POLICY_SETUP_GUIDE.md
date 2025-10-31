# Deal Scout Privacy Policy Setup Guide

**Date:** October 30, 2025
**Status:** Ready for Setup

---

## Quick Summary

This guide helps you create a GitHub Pages repository for your Deal Scout Privacy Policy. The policy will be hosted at:

```
https://{your-github-username}.github.io/dealscout-privacy/
```

---

## Option 1: GitHub Web Interface (Easiest)

### Step 1: Create Repository
1. Go to https://github.com/new
2. Enter repository name: `dealscout-privacy`
3. Select: **Public**
4. Click **Create repository**

### Step 2: Add Privacy Policy Content
1. In your new repository, click **Add file** → **Create new file**
2. Enter filename: `index.html`
3. Paste the privacy policy HTML (see below)
4. Click **Commit new file**

### Step 3: Enable GitHub Pages
1. Go to repository **Settings**
2. Click **Pages** in left sidebar
3. Under "Source", select:
   - **Branch:** main
   - **Folder:** / (root)
4. Click **Save**

### Step 4: Verify
Your privacy policy is now live at:
```
https://{your-username}.github.io/dealscout-privacy/
```

---

## Option 2: Git Command Line (Automated)

### Prerequisites
- Git installed
- GitHub authenticated: `git config --global user.email "your@email.com"`

### Step 1: Create Repository (via GitHub Web)
First, create the empty repository using the web interface (follow Option 1, Steps 1 only).

### Step 2: Clone and Setup Locally

```bash
# Clone the repository
git clone https://github.com/{your-username}/dealscout-privacy.git
cd dealscout-privacy

# Create the privacy policy file (see HTML below)
cat > index.html << 'EOF'
[PASTE THE HTML FROM SECTION BELOW]
EOF

# Commit and push
git add index.html
git commit -m "Add Privacy Policy"
git push -u origin main
```

### Step 3: Enable GitHub Pages
1. Go to repository **Settings** → **Pages**
2. Select **Branch: main** → **Folder: /**
3. Click **Save**

---

## Privacy Policy HTML Content

Copy this entire HTML block into your `index.html` file:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deal Scout - Privacy Policy</title>
    <style>
        body {
            font-family: system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
        }
        .updated {
            color: #666;
            font-size: 0.9em;
        }
        ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        li {
            margin: 8px 0;
        }
        hr {
            margin-top: 40px;
            border: none;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <h1>Deal Scout - Privacy Policy</h1>
    <p class="updated">Last Updated: October 30, 2025</p>

    <h2>1. Introduction</h2>
    <p>Deal Scout operates the application. This page informs you of our policies regarding the collection, use, and disclosure of personal data when you use our Service.</p>

    <h2>2. Information Collection and Use</h2>
    <p>We collect several different types of information for various purposes to provide and improve our Service to you.</p>
    <ul>
        <li><strong>Account Information:</strong> Username, email address, and password when you create an account</li>
        <li><strong>Profile Information:</strong> Location, search preferences, and saved listings</li>
        <li><strong>Marketplace Accounts:</strong> Authorization tokens for connected marketplaces</li>
        <li><strong>Usage Data:</strong> Browser type, operating system, and pages visited</li>
        <li><strong>Images:</strong> Photos you upload for items you wish to sell</li>
    </ul>

    <h2>3. Use of Data</h2>
    <p>Deal Scout uses the collected data for various purposes:</p>
    <ul>
        <li>To provide and maintain our Service</li>
        <li>To notify you about changes to our Service</li>
        <li>To allow you to participate in interactive features of our Service</li>
        <li>To monitor the usage of our Service</li>
        <li>To detect, prevent and address technical and security issues</li>
        <li>To provide customer support</li>
    </ul>

    <h2>4. Security of Data</h2>
    <p>The security of your data is important to us. While we strive to use commercially acceptable means to protect your personal data, we cannot guarantee its absolute security.</p>

    <h2>5. Changes to This Privacy Policy</h2>
    <p>We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the date at the top.</p>

    <h2>6. Contact Us</h2>
    <p>If you have any questions about this Privacy Policy, please contact us at support@dealscout.local</p>

    <hr>
    <p style="color: #999; font-size: 0.9em;">This Privacy Policy was automatically generated on October 30, 2025</p>
</body>
</html>
```

---

## Verification Checklist

After completing the setup:

- [ ] Repository `dealscout-privacy` created on GitHub
- [ ] `index.html` file added with privacy policy content
- [ ] GitHub Pages enabled in repository settings
- [ ] Privacy policy accessible at `https://{your-username}.github.io/dealscout-privacy/`
- [ ] Website displays correctly in browser

---

## Troubleshooting

### Privacy Policy not showing?
1. Wait 1-2 minutes for GitHub Pages to build and deploy
2. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
3. Check repository **Actions** tab for build errors

### GitHub Pages not enabled?
1. Go to **Settings** → **Pages**
2. Ensure **Source** is set to **main** branch and **/** folder
3. Click **Save** again

### Want to customize the privacy policy?
Edit `index.html` in your GitHub repository and commit the changes. GitHub Pages will automatically rebuild.

---

## Production Notes

For a production application, you may want to:
- Add HTTPS support (GitHub Pages provides this automatically)
- Link to this privacy policy from your main application
- Keep the policy updated as your data practices change
- Consider adding a Terms of Service page alongside

---

## Current Status

✅ Privacy policy HTML created and ready to deploy
✅ Setup guide provided with multiple options
⏳ Awaiting your GitHub setup (choose Option 1 or 2 above)

---

**Next Step:** Choose Option 1 (Web Interface) or Option 2 (Git CLI) and follow the steps above.
