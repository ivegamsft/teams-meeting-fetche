# Teams Meeting Fetcher — Setup & Automation Guide

Complete guide to setting up, documenting, and reproducing the Teams Meeting Fetcher environment.

---

## 🚀 Quick Start Paths

### Path 1: I'm a New Developer (5-30 minutes)

```bash
# 1. Read the quick overview
cat README.md | grep -A 20 "Bootstrap & Setup"

# 2. Follow bootstrap prompts (in order)
# Use these with Copilot or manually:
# - bootstrap-dev-env.prompt.md
# - bootstrap-teams-config.prompt.md
# - bootstrap-azure-spn.prompt.md (if using Azure)
# - bootstrap-aws-iam.prompt.md (if using AWS)
# - bootstrap-gh-workflow-creds.prompt.md (to enable CI/CD)

# 3. Run inventory to document what you've set up
python scripts/teams/run-inventory.py

# 4. You're done! Review inventory/teams-config-inventory.md
```

**Time**: ~30 minutes  
**Result**: Local dev environment fully configured

---

### Path 2: I Have an Existing Setup (5-10 minutes)

```bash
# 1. Run inventory to document current state
python scripts/teams/run-inventory.py

# 2. Review what was exported
cat inventory/teams-config-inventory.md

# 3. Commit inventory to version control
git add inventory/
git commit -m "docs: export Teams bot configuration"

# Done! Inventory is now available for:
# - Reproducing setup in new environments
# - Training new developers
# - Disaster recovery
```

**Time**: ~10 minutes  
**Result**: Complete configuration documentation

---

### Path 3: I Need to Reproduce This Setup in a New Environment

```bash
# 1. Get inventory from git history or team
git checkout -- inventory/

# 2. Review reproduction steps
cat inventory/teams-config-inventory.md | grep -A 50 "How to Reproduce"

# 3. Follow the reproduction checklist
# This walks you through recreating the entire setup

# 4. Run validation to verify setup
python scripts/teams/run-inventory.py
python scripts/graph/01-verify-setup.py

# Done! New environment matches original
```

**Time**: Varies (typically 1-2 hours depending on cloud complexity)  
**Result**: New environment with identical configuration

---

### Path 4: I Need to Check for Configuration Drift

```bash
# 1. Last known good state
git show HEAD~5:inventory/teams-config-inventory.md > /tmp/old.md

# 2. Current state
python scripts/teams/run-inventory.py

# 3. Compare
diff /tmp/old.md inventory/teams-config-inventory.md

# What changed? Users added? Policies modified?
# Take corrective action or update desired state

# 4. Commit if intentional
git add inventory/
git commit -m "docs: reconcile Teams configuration drift"
```

**Time**: ~5 minutes  
**Result**: Identify unintended changes

---

## 📖 Documentation Map

### Setup & Bootstrap Guides

These are step-by-step guides for initial setup. Use with Copilot agents or manually.

| Guide                                                                                          | Purpose                                                | Time   |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------ |
| [bootstrap-dev-env.prompt.md](.github/prompts/bootstrap-dev-env.prompt.md)                     | Local environment: Node.js, Python, AWS CLI, Azure SPN | 15 min |
| [bootstrap-teams-config.prompt.md](.github/prompts/bootstrap-teams-config.prompt.md)           | Teams: App registration, policies, webhook             | 30 min |
| [bootstrap-azure-spn.prompt.md](.github/prompts/bootstrap-azure-spn.prompt.md)                 | Azure SPN for dev + CI/CD, Key Vault                   | 20 min |
| [bootstrap-aws-iam.prompt.md](.github/prompts/bootstrap-aws-iam.prompt.md)                     | AWS IAM user, Lambda role, S3 bucket                   | 20 min |
| [bootstrap-gh-workflow-creds.prompt.md](.github/prompts/bootstrap-gh-workflow-creds.prompt.md) | GitHub Actions: AWS + Azure secrets                    | 15 min |

### Automation & Inventory

Documentation for the automated systems that audit and document your setup.

| Document                                                                            | Purpose                               |
| ----------------------------------------------------------------------------------- | ------------------------------------- |
| [TEAMS_INVENTORY_AUTOMATION.md](./docs/TEAMS_INVENTORY_AUTOMATION.md)               | How to use the inventory system       |
| [TEAMS_INVENTORY_SCRIPTS_REFERENCE.md](./docs/TEAMS_INVENTORY_SCRIPTS_REFERENCE.md) | Script architecture & troubleshooting |
| [.github/GITHUB_WORKFLOWS_SETUP.md](./.github/GITHUB_WORKFLOWS_SETUP.md)            | GitHub Actions setup guide            |

### Validation & Comparison

Documentation for validating your setup and detecting drift.

| Prompt                                                                                                         | Purpose                                           | Time   |
| -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ------ |
| [inventory-teams-config.prompt.md](.github/prompts/inventory-teams-config.prompt.md)                           | Manual audit steps (if automating isn't possible) | 20 min |
| [validate-teams-config-repeatability.prompt.md](.github/prompts/validate-teams-config-repeatability.prompt.md) | Test reproduction steps in isolated environment   | 1 hour |
| [compare-teams-config.prompt.md](.github/prompts/compare-teams-config.prompt.md)                               | Detect drift between dev/staging/prod             | 20 min |

---

## 🛠️ Automation Scripts

### Inventory Scripts

**Quick Start:**

```bash
# Windows PowerShell
.\scripts\teams\run-inventory.ps1

# All platforms (Python)
python scripts/teams/run-inventory.py

# Check only (don't run full audit)
python scripts/teams/run-inventory.py --check-only

# Archive existing inventory
python scripts/teams/run-inventory.py --archive-only
```

**Scripts:**

- `scripts/teams/inventory-teams-config.py` — Core audit logic in Python
- `scripts/teams/run-inventory.ps1` — Windows PowerShell wrapper with checks
- `scripts/teams/run-inventory.py` — Cross-platform wrapper with checks

### GitHub Actions Scripts

For setting up credentials:

```bash
# AWS IAM automation
bash scripts/setup-github-aws-iam.sh
# or
powershell .\scripts\setup-github-aws-iam.ps1

# Azure SPN automation
bash scripts/setup-github-azure-spn.sh
# or
powershell .\scripts\setup-github-azure-spn.ps1

# Verify all secrets configured
bash scripts/verify-github-secrets.sh
# or
powershell .\scripts\verify-github-secrets.ps1
```

---

## 📋 Workflow Examples

### New Developer Joining Project (Day 1)

```bash
# 1. Clone repo
git clone https://github.com/ivegamsft/teams-meeting-fetcher
cd teams-meeting-fetcher

# 2. Get .env.local from team (via secure channel - never email!)
# Place in repo root

# 3. Follow bootstrap-dev-env.prompt.md
# This sets up everything locally

# 4. Read inventory to understand current setup
python scripts/teams/run-inventory.py
cat inventory/teams-config-inventory.md

# 5. Verify everything works
npm test
python scripts/graph/01-verify-setup.py

# Done! You're productive
```

### Adding New User to Monitoring Group

```bash
# 1. Request to be added to ENTRA_GROUP_ID
# (Admin adds user to security group)

# 2. Wait 5 minutes for replication

# 3. Verify your access
python scripts/graph/01-verify-setup.py

# 4. Update inventory to document change
python scripts/teams/run-inventory.py

# 5. Commit
git add inventory/
git commit -m "docs: add new user to monitoring group"
```

### Deploying to New Environment (Disaster Recovery)

```bash
# 1. Get inventory from git
git log --oneline -- inventory/

# 2. Check out last known good state
git checkout abc1234 -- inventory/

# 3. Read reproduction steps
less inventory/teams-config-inventory.md

# 4. Follow "How to Reproduce" section
# This is a complete walkthrough

# 5. Verify setup matches
python scripts/teams/run-inventory.py
python scripts/graph/01-verify-setup.py

# 6. Update inventory (new environment will have different IDs)
python scripts/teams/run-inventory.py

# 7. Commit new inventory
git add inventory/
git commit -m "docs: deploy to new environment"
```

### Monthly Audit

```bash
# 1. Run inventory to check current state
python scripts/teams/run-inventory.py

# 2. See what changed since last month
git diff HEAD~1 -- inventory/teams-config-inventory.md

# 3. If changes are expected (new users, policy updates):
git add inventory/
git commit -m "docs: monthly Teams inventory audit"

# 4. If changes are unexpected (drift):
# Alert team and investigate
# Either update actual config or revert to desired state
```

---

## 🔍 Where to Find Things

### I need to...

**...set up from scratch**
→ Read [bootstrap-dev-env.prompt.md](.github/prompts/bootstrap-dev-env.prompt.md)

**...understand the current Teams setup**
→ Run `python scripts/teams/run-inventory.py` then read `inventory/teams-config-inventory.md`

**...reproduce this setup in a new environment**
→ Get inventory, then read "How to Reproduce" section at bottom

**...detect if anything changed**
→ Run `python scripts/teams/run-inventory.py` and `git diff`

**...test that a reproduction works**
→ Follow [validate-teams-config-repeatability.prompt.md](.github/prompts/validate-teams-config-repeatability.prompt.md)

**...compare development vs production**
→ Use [compare-teams-config.prompt.md](.github/prompts/compare-teams-config.prompt.md)

**...set up GitHub Actions**
→ Run setup scripts or read [.github/GITHUB_WORKFLOWS_SETUP.md](./.github/GITHUB_WORKFLOWS_SETUP.md)

**...troubleshoot an error**
→ Check [TEAMS_INVENTORY_SCRIPTS_REFERENCE.md](./docs/TEAMS_INVENTORY_SCRIPTS_REFERENCE.md)

---

## 📊 Quick Reference

### Essential Environment Variables

```bash
# Always required
GRAPH_TENANT_ID=<your-azure-tenant-id>
GRAPH_CLIENT_ID=<your-app-id>
ENTRA_GROUP_ID=<your-group-id>

# For local development
AWS_PROFILE=tmf-dev
AWS_REGION=us-east-1
WEBHOOK_AUTH_SECRET=<random-string>

# For GitHub Actions (configured as secrets)
AWS_ACCESS_KEY_ID=<from-aws-iam>
AWS_SECRET_ACCESS_KEY=<from-aws-iam>
AZURE_CREDENTIALS=<json-from-azure>
AZURE_SUBSCRIPTION_ID=<your-subscription>
EXPECTED_TENANT_ID=<your-tenant>
```

### Files to Never Commit

```bash
.env.local              # Local secrets (in .gitignore)
.aws/credentials        # AWS credentials (in .gitignore)
teams-app-backup.json   # Old manifests (already in .gitignore)
*.key                   # SSL/TLS keys (in .gitignore)
```

### Files to Always Keep Updated

```bash
inventory/teams-config-inventory.md     # Audit documentation
.github/GITHUB_WORKFLOWS_SETUP.md        # Workflow setup
README.md                                # Project overview
```

---

## 🤝 Contributing Setup Documentation

When you add a new step, tool, or configuration:

1. **Document it** in the appropriate bootstrap prompt
2. **Update the automation** script to export it
3. **Test reproduction** using [validate-teams-config-repeatability.prompt.md](.github/prompts/validate-teams-config-repeatability.prompt.md)
4. **Commit inventory** with the changes

This ensures the setup stays repeatable and documented.

---

## 📚 Related Documentation

- [system-specification.md](./specs/system-specification.md) — Architecture & design
- [setup-guide.md](./specs/setup-guide.md) — Detailed setup instructions
- [DEPLOYMENT.md](./DEPLOYMENT.md) — Deployment procedures
- [Teams-Meeting-Fetcher-Workflow.ipynb](./Teams-Meeting-Fetcher-Workflow.ipynb) — Interactive notebook walkthrough

---

## ❓ FAQ

**Q: Do I need to run inventory every time I make a change?**  
A: No, but it's good practice to run it after major changes and commit the updated documentation. We recommend weekly or on-demand.

**Q: Can I use the inventory to onboard a new team member?**  
A: Absolutely! Share `inventory/teams-config-inventory.md` and `bootstrap-dev-env.prompt.md`. New member can follow "How to Reproduce" section to recreate setup.

**Q: What if I can't run the automation scripts?**  
A: Follow the manual steps in the corresponding `.prompt.md` file in `.github/prompts/`.

**Q: How do I know if my setup matches production?**  
A: Compare inventories using [compare-teams-config.prompt.md](.github/prompts/compare-teams-config.prompt.md) — it shows exactly what's different.

**Q: Can I automate inventory in GitHub Actions?**  
A: Yes! See [TEAMS_INVENTORY_AUTOMATION.md](./docs/TEAMS_INVENTORY_AUTOMATION.md) for a sample workflow.

---

## 🆘 Need Help?

1. **Setup Issue?** → Check `.github/prompts/` for step-by-step guide
2. **Script Error?** → See [TEAMS_INVENTORY_SCRIPTS_REFERENCE.md](./docs/TEAMS_INVENTORY_SCRIPTS_REFERENCE.md)
3. **Configuration Drift?** → Run inventory and compare: `git diff`
4. **Can't Reproduce?** → Follow [validate-teams-config-repeatability.prompt.md](.github/prompts/validate-teams-config-repeatability.prompt.md)

---

**Last Updated**: February 16, 2026  
**Status**: Complete setup & automation documentation ready  
**Next**: Execute bootstrap prompts → Build → Deploy
