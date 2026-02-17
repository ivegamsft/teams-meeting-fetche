#!/usr/bin/env pwsh
# Setup script for Azure Service Principal creation (PowerShell)
# Run this script to automate Azure SPN setup for GitHub Actions on Windows

$ErrorActionPreference = "Stop"

Write-Host "🔐 Azure Service Principal Setup for GitHub Actions" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Azure CLI is installed
try {
    $null = az version
}
catch {
    Write-Host "❌ Azure CLI is not installed." -ForegroundColor Red
    Write-Host "   Download: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Azure CLI is installed" -ForegroundColor Green
Write-Host ""

# Check Azure credentials
try {
    $accountInfo = az account show | ConvertFrom-Json
}
catch {
    Write-Host "❌ Azure CLI is not authenticated. Run: az login" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Azure CLI is authenticated" -ForegroundColor Green
Write-Host ""

$SUBSCRIPTION_ID = $accountInfo.id
$SUBSCRIPTION_NAME = $accountInfo.name
$TENANT_ID = $accountInfo.tenantId

Write-Host "📍 Subscription: $SUBSCRIPTION_NAME" -ForegroundColor Cyan
Write-Host "📍 Subscription ID: $SUBSCRIPTION_ID" -ForegroundColor Cyan
Write-Host "📍 Tenant ID: $TENANT_ID" -ForegroundColor Cyan
Write-Host ""

$SP_NAME = "tmf-github-actions"

Write-Host "📝 Creating Service Principal: $SP_NAME" -ForegroundColor Cyan
Write-Host ""

# Check if service principal already exists
try {
    $existingSP = az ad sp list --display-name $SP_NAME --query "[0].id" --output tsv
    if ($existingSP) {
        Write-Host "⚠️  Service Principal '$SP_NAME' already exists." -ForegroundColor Yellow
        $response = Read-Host "Delete and recreate it? (yes/no)"
        if ($response -eq "yes") {
            Write-Host "Deleting existing service principal..." -ForegroundColor Cyan
            az ad sp delete --id $existingSP
            Write-Host "✅ Deleted" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Client secrets cannot be retrieved for existing SPNs." -ForegroundColor Yellow
            Write-Host "   You need to create a new client secret in Azure Portal:" -ForegroundColor Yellow
            Write-Host "   1. Go to Azure Portal > Entra ID > App registrations" -ForegroundColor Yellow
            Write-Host "   2. Find '$SP_NAME'" -ForegroundColor Yellow
            Write-Host "   3. Go to Certificates & secrets" -ForegroundColor Yellow
            Write-Host "   4. Click 'New client secret'" -ForegroundColor Yellow
            exit 0
        }
    }
}
catch {
    # No existing SP found, continue
}

Write-Host ""
Write-Host "🔑 Creating Service Principal and credentials..." -ForegroundColor Cyan
Write-Host ""

# Create the service principal with Contributor role
$spJson = az ad sp create-for-rbac `
    --name "$SP_NAME" `
    --role Contributor `
    --scopes "/subscriptions/$SUBSCRIPTION_ID" `
    --json-auth

$spCredentials = $spJson | ConvertFrom-Json

Write-Host "✅ Service Principal created successfully!" -ForegroundColor Green
Write-Host ""

$CLIENT_ID = $spCredentials.clientId
$CLIENT_SECRET = $spCredentials.clientSecret
$TENANT = $spCredentials.tenantId

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "🔐 YOUR AZURE CREDENTIALS (Save these securely!)" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""
Write-Host "Complete JSON (for AZURE_CREDENTIALS secret):" -ForegroundColor Cyan
Write-Host ($spJson | ConvertFrom-Json | ConvertTo-Json -Compress)
Write-Host ""
Write-Host "Individual values:" -ForegroundColor Cyan
Write-Host "  Client ID: $CLIENT_ID"
Write-Host "  Client Secret: $CLIENT_SECRET"
Write-Host "  Subscription ID: $SUBSCRIPTION_ID"
Write-Host "  Tenant ID: $TENANT"
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
        Write-Host "Then run the commands below to add secrets:" -ForegroundColor Cyan
        exit 0
    }

    Write-Host "Adding to GitHub secrets..." -ForegroundColor Cyan
    
    $jsonCompact = $spJson | ConvertFrom-Json | ConvertTo-Json -Compress
    gh secret set AZURE_CREDENTIALS --body "$jsonCompact"
    Write-Host "✅ AZURE_CREDENTIALS added" -ForegroundColor Green
    
    gh secret set AZURE_CLIENT_ID --body "$CLIENT_ID"
    Write-Host "✅ AZURE_CLIENT_ID added" -ForegroundColor Green
    
    gh secret set AZURE_CLIENT_SECRET --body "$CLIENT_SECRET"
    Write-Host "✅ AZURE_CLIENT_SECRET added" -ForegroundColor Green
    
    gh secret set AZURE_SUBSCRIPTION_ID --body "$SUBSCRIPTION_ID"
    Write-Host "✅ AZURE_SUBSCRIPTION_ID added" -ForegroundColor Green
    
    gh secret set EXPECTED_TENANT_ID --body "$TENANT"
    Write-Host "✅ EXPECTED_TENANT_ID added" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "✅ All secrets added to GitHub!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "📝 To add these as GitHub secrets manually:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Using GitHub CLI:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  gh secret set AZURE_CREDENTIALS --body '$(($spJson | ConvertFrom-Json | ConvertTo-Json -Compress))'"
    Write-Host ""
    Write-Host "  gh secret set AZURE_CLIENT_ID --body '$CLIENT_ID'"
    Write-Host "  gh secret set AZURE_CLIENT_SECRET --body '$CLIENT_SECRET'"
    Write-Host "  gh secret set AZURE_SUBSCRIPTION_ID --body '$SUBSCRIPTION_ID'"
    Write-Host "  gh secret set EXPECTED_TENANT_ID --body '$TENANT'"
    Write-Host ""
    Write-Host "Or via GitHub UI:" -ForegroundColor Cyan
    Write-Host "  1. Go to Settings > Secrets and variables > Actions"
    Write-Host "  2. Click 'New repository secret' for each value above"
}

Write-Host ""
Write-Host "✅ Azure Service Principal setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Note: The client secret expires in 1 year. Set a reminder to rotate it." -ForegroundColor Yellow
