# Deal Scout Privacy Policy - GitHub Pages Setup
# Execute idempotently - safe to run multiple times

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deal Scout Privacy Policy Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Prerequisites
Write-Host "[1/6] Checking prerequisites..." -ForegroundColor Yellow
$gitExists = (git --version 2>$null) -ne $null
$ghExists = (gh --version 2>$null) -ne $null

if (-not $gitExists) {
    Write-Host "❌ Git not found. Please install Git from https://git-scm.com/" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Git found" -ForegroundColor Green

if (-not $ghExists) {
    Write-Host "❌ GitHub CLI not found. Please install from https://cli.github.com/" -ForegroundColor Red
    exit 1
}
Write-Host "✓ GitHub CLI found" -ForegroundColor Green

# Step 2: Check GitHub Authentication
Write-Host "[2/6] Checking GitHub authentication..." -ForegroundColor Yellow
$ghAuth = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Not authenticated with GitHub. Run: gh auth login" -ForegroundColor Red
    exit 1
}
Write-Host "✓ GitHub authenticated" -ForegroundColor Green

# Get GitHub username
$githubUser = gh api user --jq '.login' 2>$null
if (-not $githubUser) {
    Write-Host "❌ Could not detect GitHub username" -ForegroundColor Red
    exit 1
}
Write-Host "✓ GitHub user: $githubUser" -ForegroundColor Green

# Step 3: Create Repository
Write-Host "[3/6] Setting up repository..." -ForegroundColor Yellow
$repoName = "dealscout-privacy"
$repoExists = gh repo view $repoName 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Repository already exists" -ForegroundColor Green
} else {
    Write-Host "Creating new repository: $repoName" -ForegroundColor Cyan
    gh repo create $repoName --public 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Repository created" -ForegroundColor Green
    } else {
        Write-Host "⚠ Repository might already exist, continuing..." -ForegroundColor Yellow
    }
}

# Step 4: Clone and Setup Repository
Write-Host "[4/6] Setting up local repository..." -ForegroundColor Yellow
$tempDir = Join-Path $env:TEMP "dealscout-privacy"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force 2>$null
}
git clone "https://github.com/$githubUser/$repoName.git" $tempDir 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ Clone failed, initializing local repo..." -ForegroundColor Yellow
    $tempDir = New-Item -ItemType Directory -Path $tempDir -Force | Select-Object -ExpandProperty FullName
    Set-Location $tempDir
    git init
    git config user.email "support@dealscout.local"
    git config user.name "Deal Scout"
    git remote add origin "https://github.com/$githubUser/$repoName.git" 2>$null
} else {
    Write-Host "✓ Repository cloned" -ForegroundColor Green
    Set-Location $tempDir
}

# Step 5: Create Privacy Policy Content
Write-Host "[5/6] Creating Privacy Policy..." -ForegroundColor Yellow

# Create HTML file directly
$indexPath = Join-Path $tempDir "index.html"

# Write HTML file with proper escaping
@"
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
"@ | Set-Content -Path $indexPath -Encoding UTF8

Write-Host "✓ Privacy Policy created at $indexPath" -ForegroundColor Green

# Step 6: Push to GitHub
Write-Host "[6/6] Committing and pushing to GitHub..." -ForegroundColor Yellow
git add index.html 2>&1 | Out-Null
git commit -m "Add Privacy Policy" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "✓ No changes to commit (already up to date)" -ForegroundColor Green
} else {
    Write-Host "✓ Privacy Policy committed" -ForegroundColor Green
}

git push -u origin main 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ Push to main failed, trying master..." -ForegroundColor Yellow
    git push -u origin master 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠ Initial push may require manual setup" -ForegroundColor Yellow
    } else {
        Write-Host "✓ Pushed to master branch" -ForegroundColor Green
    }
} else {
    Write-Host "✓ Pushed to GitHub successfully" -ForegroundColor Green
}

# Step 7: Enable GitHub Pages
Write-Host "[7/7] Enabling GitHub Pages..." -ForegroundColor Yellow
$pagesStatus = gh api repos/$githubUser/$repoName/pages --jq '.source.branch' 2>$null
if ($pagesStatus) {
    Write-Host "✓ GitHub Pages already enabled on branch: $pagesStatus" -ForegroundColor Green
} else {
    Write-Host "Attempting to enable GitHub Pages..." -ForegroundColor Cyan
    gh api repos/$githubUser/$repoName/pages -X POST -f source[branch]=main -f source[path]=/ 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ GitHub Pages enabled" -ForegroundColor Green
    } else {
        Write-Host "⚠ GitHub Pages may already be configured or may require manual setup" -ForegroundColor Yellow
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Privacy Policy URL:" -ForegroundColor Yellow
Write-Host "https://$githubUser.github.io/$repoName/" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repository: https://github.com/$githubUser/$repoName" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: GitHub Pages may take a few minutes to become available after setup." -ForegroundColor DarkYellow
Write-Host ""
