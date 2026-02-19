#!/bin/bash
# Setup script for Azure Service Principal creation
# Run this script to automate Azure SPN setup for GitHub Actions

set -e

echo "🔐 Azure Service Principal Setup for GitHub Actions"
echo "===================================================="
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first:"
    echo "   https://learn.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check Azure credentials
if ! az account show &> /dev/null; then
    echo "❌ Azure CLI is not authenticated. Run: az login"
    exit 1
fi

echo "✅ Azure CLI is authenticated"
echo ""

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

echo "📍 Subscription: $SUBSCRIPTION_NAME"
echo "📍 Subscription ID: $SUBSCRIPTION_ID"
echo "📍 Tenant ID: $TENANT_ID"
echo ""

# Service Principal name
SP_NAME="tmf-github-actions"

echo "📝 Creating Service Principal: $SP_NAME"
echo ""

# Check if service principal already exists
if az ad sp list --display-name $SP_NAME --query "[0].id" -o tsv &> /dev/null; then
    EXISTING_SP=$(az ad sp list --display-name $SP_NAME --query "[0].id" -o tsv)
    if [ ! -z "$EXISTING_SP" ]; then
        echo "⚠️  Service Principal '$SP_NAME' already exists."
        read -p "Do you want to delete and recreate it? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Deleting existing service principal..."
            az ad sp delete --id $EXISTING_SP
            echo "✅ Deleted"
        else
            echo "Keeping existing SPN. Retrieving credentials..."
            # Note: We can't retrieve the password for an existing SPN
            # User will need to create a new one or use Azure Portal
            echo ""
            echo "⚠️  Client secrets cannot be retrieved for existing SPNs."
            echo "   You need to create a new client secret in Azure Portal:"
            echo "   1. Go to Azure Portal > Entra ID > App registrations"
            echo "   2. Find '$SP_NAME'"
            echo "   3. Go to Certificates & secrets"
            echo "   4. Click 'New client secret'"
            exit 0
        fi
    fi
fi

echo ""
echo "🔑 Creating Service Principal and credentials..."
echo ""

# Create the service principal with Contributor role
SP_JSON=$(az ad sp create-for-rbac \
    --name "$SP_NAME" \
    --role Contributor \
    --scopes "/subscriptions/$SUBSCRIPTION_ID" \
    --json-auth)

echo "✅ Service Principal created successfully!"
echo ""

# Extract credentials
CLIENT_ID=$(echo $SP_JSON | jq -r '.clientId')
CLIENT_SECRET=$(echo $SP_JSON | jq -r '.clientSecret')
TENANT=$(echo $SP_JSON | jq -r '.tenantId')

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 YOUR AZURE CREDENTIALS (Save these securely!)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Complete JSON (for AZURE_CREDENTIALS secret):"
echo "$SP_JSON" | jq '.' | sed 's/^/  /'
echo ""
echo "Individual values:"
echo "  Client ID: $CLIENT_ID"
echo "  Client Secret: $CLIENT_SECRET"
echo "  Subscription ID: $SUBSCRIPTION_ID"
echo "  Tenant ID: $TENANT"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Option to add to GitHub secrets
read -p "Do you have GitHub CLI installed and want to add these as secrets? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if ! command -v gh &> /dev/null; then
        echo "❌ GitHub CLI is not installed."
        echo "   Install it: https://cli.github.com"
        echo ""
        echo "Then run the commands below to add secrets:"
    else
        echo "Adding to GitHub secrets..."
        
        # Add secrets
        gh secret set AZURE_CREDENTIALS --body "$(echo $SP_JSON | jq -c '.')"
        echo "✅ AZURE_CREDENTIALS added"
        
        gh secret set AZURE_CLIENT_ID --body "$CLIENT_ID"
        echo "✅ AZURE_CLIENT_ID added"
        
        gh secret set AZURE_CLIENT_SECRET --body "$CLIENT_SECRET"
        echo "✅ AZURE_CLIENT_SECRET added"
        
        gh secret set AZURE_SUBSCRIPTION_ID --body "$SUBSCRIPTION_ID"
        echo "✅ AZURE_SUBSCRIPTION_ID added"
        
        gh secret set EXPECTED_TENANT_ID --body "$TENANT"
        echo "✅ EXPECTED_TENANT_ID added"
        
        echo ""
        echo "✅ All secrets added to GitHub!"
    fi
else
    echo ""
    echo "📝 To add these as GitHub secrets manually:"
    echo ""
    echo "Using GitHub CLI:"
    echo ""
    echo "  gh secret set AZURE_CREDENTIALS --body '"
    echo $SP_JSON | jq -c '.' | sed "s/^/  /"
    echo "  '"
    echo ""
    echo "  gh secret set AZURE_CLIENT_ID --body '$CLIENT_ID'"
    echo "  gh secret set AZURE_CLIENT_SECRET --body '$CLIENT_SECRET'"
    echo "  gh secret set AZURE_SUBSCRIPTION_ID --body '$SUBSCRIPTION_ID'"
    echo "  gh secret set EXPECTED_TENANT_ID --body '$TENANT'"
    echo ""
    echo "Or via GitHub UI:"
    echo "  1. Go to Settings > Secrets and variables > Actions"
    echo "  2. Click 'New repository secret' for each value above"
fi

echo ""
echo "✅ Azure Service Principal setup complete!"
echo ""
echo "📝 Note: The client secret expires in 1 year. Set a reminder to rotate it."
