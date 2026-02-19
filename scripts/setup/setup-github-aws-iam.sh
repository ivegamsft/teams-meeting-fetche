#!/bin/bash
# Setup script for AWS IAM user creation and credential generation
# Run this script to automate AWS IAM setup for GitHub Actions

set -e

echo "🔐 AWS IAM Setup for GitHub Actions"
echo "===================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first:"
    echo "   https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI is not configured. Run: aws configure"
    exit 1
fi

echo "✅ AWS CLI is configured"
echo ""

# Get current AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📍 AWS Account ID: $ACCOUNT_ID"
echo ""

# User name for the IAM user
IAM_USER="tmf-github-actions"

echo "📝 Creating IAM user: $IAM_USER"
echo ""

# Check if user already exists
if aws iam get-user --user-name $IAM_USER &> /dev/null; then
    echo "⚠️  IAM user '$IAM_USER' already exists. Skipping creation."
    echo "   To recreate, delete it first: aws iam delete-user --user-name $IAM_USER"
else
    echo "Creating user..."
    aws iam create-user --user-name $IAM_USER
    echo "✅ User created: $IAM_USER"
fi

echo ""
echo "📌 Attaching Administrator policy..."
aws iam attach-user-policy \
    --user-name $IAM_USER \
    --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

echo "✅ Administrator policy attached"
echo ""

# Check for existing access keys
EXISTING_KEYS=$(aws iam list-access-keys --user-name $IAM_USER --query 'AccessKeyMetadata[*].AccessKeyId' --output text)

if [ ! -z "$EXISTING_KEYS" ]; then
    echo "⚠️  Existing access keys found: $EXISTING_KEYS"
    read -p "Do you want to delete these and create new ones? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for KEY in $EXISTING_KEYS; do
            echo "Deleting access key: $KEY"
            aws iam delete-access-key --user-name $IAM_USER --access-key-id $KEY
        done
    else
        echo "Keeping existing keys. Rerunning this script to get them."
        exit 0
    fi
fi

echo ""
echo "🔑 Creating new access key..."
CREDENTIALS=$(aws iam create-access-key --user-name $IAM_USER --output json)

ACCESS_KEY_ID=$(echo $CREDENTIALS | jq -r '.AccessKey.AccessKeyId')
SECRET_ACCESS_KEY=$(echo $CREDENTIALS | jq -r '.AccessKey.SecretAccessKey')

echo ""
echo "✅ Access key created successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 YOUR AWS CREDENTIALS (Save these securely!)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Access Key ID:"
echo "$ACCESS_KEY_ID"
echo ""
echo "Secret Access Key:"
echo "$SECRET_ACCESS_KEY"
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
        echo "Then run:"
        echo "  gh secret set AWS_ACCESS_KEY_ID --body '$ACCESS_KEY_ID'"
        echo "  gh secret set AWS_SECRET_ACCESS_KEY --body '$SECRET_ACCESS_KEY'"
    else
        echo "Adding to GitHub secrets..."
        gh secret set AWS_ACCESS_KEY_ID --body "$ACCESS_KEY_ID"
        gh secret set AWS_SECRET_ACCESS_KEY --body "$SECRET_ACCESS_KEY"
        echo "✅ Secrets added to GitHub!"
    fi
else
    echo ""
    echo "📝 To add these as GitHub secrets manually:"
    echo ""
    echo "Using GitHub CLI:"
    echo "  gh secret set AWS_ACCESS_KEY_ID --body '$ACCESS_KEY_ID'"
    echo "  gh secret set AWS_SECRET_ACCESS_KEY --body '$SECRET_ACCESS_KEY'"
    echo ""
    echo "Or via GitHub UI:"
    echo "  1. Go to Settings > Secrets and variables > Actions"
    echo "  2. Click 'New repository secret'"
    echo "  3. Add AWS_ACCESS_KEY_ID"
    echo "  4. Add AWS_SECRET_ACCESS_KEY"
fi

echo ""
echo "✅ AWS IAM setup complete!"
