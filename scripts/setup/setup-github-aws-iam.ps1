#!/usr/bin/env pwsh
# Setup script for AWS IAM user creation and credential generation (PowerShell)
# Run this script to automate AWS IAM setup for GitHub Actions on Windows

$ErrorActionPreference = "Stop"

Write-Host "🔐 AWS IAM Setup for GitHub Actions" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS CLI is installed
try {
    $null = aws --version
}
catch {
    Write-Host "❌ AWS CLI is not installed." -ForegroundColor Red
    Write-Host "   Download: https://aws.amazon.com/cli/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ AWS CLI is installed" -ForegroundColor Green
Write-Host ""

# Check AWS credentials
try {
    $accountInfo = aws sts get-caller-identity --output json | ConvertFrom-Json
}
catch {
    Write-Host "❌ AWS CLI is not configured. Run: aws configure" -ForegroundColor Red
    exit 1
}

Write-Host "✅ AWS CLI is configured" -ForegroundColor Green
Write-Host "📍 AWS Account ID: $($accountInfo.Account)" -ForegroundColor Cyan
Write-Host ""

$IAM_USER = "tmf-github-actions"

Write-Host "📝 Creating IAM user: $IAM_USER" -ForegroundColor Cyan
Write-Host ""

# Check if user already exists
try {
    $null = aws iam get-user --user-name $IAM_USER
    Write-Host "⚠️  IAM user '$IAM_USER' already exists." -ForegroundColor Yellow
    Write-Host "   To recreate, delete first: aws iam delete-user --user-name $IAM_USER" -ForegroundColor Yellow
    
    $response = Read-Host "Delete and recreate? (yes/no)"
    if ($response -eq "yes") {
        Write-Host "Deleting user and access keys..."
        $keys = aws iam list-access-keys --user-name $IAM_USER --query 'AccessKeyMetadata[*].AccessKeyId' --output text
        foreach ($key in $keys.Split()) {
            aws iam delete-access-key --user-name $IAM_USER --access-key-id $key
        }
        aws iam delete-user --user-name $IAM_USER
        Write-Host "✅ User deleted" -ForegroundColor Green
    } else {
        Write-Host "Keeping existing user. Retrieving credentials..." -ForegroundColor Yellow
    }
}
catch {
    Write-Host "Creating user..." -ForegroundColor Cyan
    $null = aws iam create-user --user-name $IAM_USER
    Write-Host "✅ User created: $IAM_USER" -ForegroundColor Green
}

Write-Host ""
Write-Host "📌 Attaching Administrator policy..." -ForegroundColor Cyan
$null = aws iam attach-user-policy `
    --user-name $IAM_USER `
    --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

Write-Host "✅ Administrator policy attached" -ForegroundColor Green
Write-Host ""

# Check for existing access keys
$existingKeys = aws iam list-access-keys --user-name $IAM_USER --query 'AccessKeyMetadata[*].AccessKeyId' --output text

if ($existingKeys) {
    Write-Host "⚠️  Existing access keys found: $existingKeys" -ForegroundColor Yellow
    $response = Read-Host "Delete and create new ones? (yes/no)"
    if ($response -eq "yes") {
        foreach ($key in $existingKeys.Split()) {
            Write-Host "Deleting access key: $key" -ForegroundColor Cyan
            aws iam delete-access-key --user-name $IAM_USER --access-key-id $key
        }
    } else {
        Write-Host "Keeping existing keys." -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "🔑 Creating new access key..." -ForegroundColor Cyan
$credentialsJson = aws iam create-access-key --user-name $IAM_USER --output json
$credentials = $credentialsJson | ConvertFrom-Json

$ACCESS_KEY_ID = $credentials.AccessKey.AccessKeyId
$SECRET_ACCESS_KEY = $credentials.AccessKey.SecretAccessKey

Write-Host ""
Write-Host "✅ Access key created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "🔐 YOUR AWS CREDENTIALS (Save these securely!)" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""
Write-Host "Access Key ID:" -ForegroundColor Cyan
Write-Host "$ACCESS_KEY_ID"
Write-Host ""
Write-Host "Secret Access Key:" -ForegroundColor Cyan
Write-Host "$SECRET_ACCESS_KEY"
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""

# Option to add to GitHub secrets
$addSecrets = Read-Host "Do you have GitHub CLI installed and want to add these as secrets? (yes/no)"

if ($addSecrets -eq "yes") {
    try {
        $null = gh --version
    }
    catch {
        Write-Host "❌ GitHub CLI is not installed." -ForegroundColor Red
        Write-Host "   Install: https://cli.github.com" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Then run:" -ForegroundColor Cyan
        Write-Host "  gh secret set AWS_ACCESS_KEY_ID --body '$ACCESS_KEY_ID'" 
        Write-Host "  gh secret set AWS_SECRET_ACCESS_KEY --body '$SECRET_ACCESS_KEY'"
        exit 0
    }

    Write-Host "Adding to GitHub secrets..." -ForegroundColor Cyan
    gh secret set AWS_ACCESS_KEY_ID --body "$ACCESS_KEY_ID"
    gh secret set AWS_SECRET_ACCESS_KEY --body "$SECRET_ACCESS_KEY"
    Write-Host "✅ Secrets added to GitHub!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "📝 To add these as GitHub secrets manually:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Using GitHub CLI:" -ForegroundColor Cyan
    Write-Host "  gh secret set AWS_ACCESS_KEY_ID --body '$ACCESS_KEY_ID'"
    Write-Host "  gh secret set AWS_SECRET_ACCESS_KEY --body '$SECRET_ACCESS_KEY'"
    Write-Host ""
    Write-Host "Or via GitHub UI:" -ForegroundColor Cyan
    Write-Host "  1. Go to Settings > Secrets and variables > Actions"
    Write-Host "  2. Click 'New repository secret'"
    Write-Host "  3. Add AWS_ACCESS_KEY_ID"
    Write-Host "  4. Add AWS_SECRET_ACCESS_KEY"
}

Write-Host ""
Write-Host "✅ AWS IAM setup complete!" -ForegroundColor Green
