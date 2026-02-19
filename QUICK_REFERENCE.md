# Quick Reference Card — Teams Bot Setup & Inventory

**Print this or bookmark for quick access!**

---

## 🚀 I Just Cloned the Repo

```bash
# 1. Install dependencies
npm install && pip install -r test/requirements.txt

# 2. Configure environment
# Get .env.local from team (never email secrets!)
cat .env.local

# 3. Verify setup
python scripts/graph/01-verify-setup.py

# 4. Understand what's configured
python scripts/teams/run-inventory.py
cat inventory/teams-config-inventory.md
```

---

## ⚙️ I Need to Set Something Up

| Task                        | Command                        | Docs                                                                                           |
| --------------------------- | ------------------------------ | ---------------------------------------------------------------------------------------------- |
| **Local dev environment**   | Follow prompt in agent         | [bootstrap-dev-env.prompt.md](.github/prompts/bootstrap-dev-env.prompt.md)                     |
| **Teams bot & policies**    | Follow prompt in agent         | [bootstrap-teams-config.prompt.md](.github/prompts/bootstrap-teams-config.prompt.md)           |
| **Azure Service Principal** | `az ad sp create-for-rbac ...` | [bootstrap-azure-spn.prompt.md](.github/prompts/bootstrap-azure-spn.prompt.md)                 |
| **AWS IAM user**            | `aws iam create-user ...`      | [bootstrap-aws-iam.prompt.md](.github/prompts/bootstrap-aws-iam.prompt.md)                     |
| **GitHub Actions secrets**  | Run setup script               | [bootstrap-gh-workflow-creds.prompt.md](.github/prompts/bootstrap-gh-workflow-creds.prompt.md) |

---

## 🔍 I Need to Understand Current Setup

```bash
# Export complete configuration
python scripts/teams/run-inventory.py

# Read the generated documentation
cat inventory/teams-config-inventory.md

# Review what was exported
ls -lah inventory/
```

---

## 🔄 I Need to Check for Configuration Changes

```bash
# See what changed since last time
git diff HEAD~1 -- inventory/teams-config-inventory.md

# Check entire history
git log --oneline -- inventory/teams-config-inventory.md

# If changes are unexpected:
# 1. Run inventory again
python scripts/teams/run-inventory.py

# 2. Compare again
git diff HEAD -- inventory/
```

---

## 📋 I Need to Reproduce This Setup Elsewhere

```bash
# 1. Get the inventory
git checkout -- inventory/

# 2. Read reproduction steps
less inventory/teams-config-inventory.md
# Look for: "How to Reproduce This Setup"

# 3. Follow the checklist

# 4. Verify it worked
python scripts/teams/run-inventory.py
python scripts/graph/01-verify-setup.py

# 5. Commit new inventory (new environment = new IDs)
git add inventory/
git commit -m "docs: export Teams config in new environment"
```

---

## 🆘 I Got an Error

| Error                                      | Quick Fix                                                          |
| ------------------------------------------ | ------------------------------------------------------------------ |
| `.env.local not found`                     | Get from team via secure channel                                   |
| `GRAPH_CLIENT_ID=<REPLACE_ME>`             | Update .env.local with real values                                 |
| `Azure CLI not found`                      | Install: `brew install azure-cli` or download from aka.ms/azurecli |
| `Python not found`                         | Install from python.org or use package manager                     |
| `Command failed: insufficient permissions` | You need Application Administrator or equivalent role              |
| Script shows warnings but continues        | It skips sections with missing env vars—that's okay                |

---

## 📚 Where to Find Documentation

| Need Help With              | See                                                                                   |
| --------------------------- | ------------------------------------------------------------------------------------- |
| Setting up from scratch     | [`SETUP_AND_AUTOMATION_GUIDE.md`](./docs/SETUP_AND_AUTOMATION_GUIDE.md)               |
| Understanding current state | Run `python scripts/teams/run-inventory.py`                                           |
| Bootstrap prompts           | [`.github/prompts/`](.github/prompts/) (5 files)                                      |
| Automation scripts          | [`scripts/teams/`](./scripts/teams/) (3 files)                                        |
| Detailed automation guide   | [`TEAMS_INVENTORY_AUTOMATION.md`](./docs/TEAMS_INVENTORY_AUTOMATION.md)               |
| Script troubleshooting      | [`TEAMS_INVENTORY_SCRIPTS_REFERENCE.md`](./docs/TEAMS_INVENTORY_SCRIPTS_REFERENCE.md) |
| General setup               | [`README.md`](./README.md) → "Bootstrap & Setup" section                              |

---

## 🎯 Essential Files You'll Use Often

```bash
# Configuration (update with real values)
.env.local

# Documentation
inventory/teams-config-inventory.md          # Current state
.github/prompts/bootstrap-*.prompt.md        # Setup guides

# Scripts
scripts/teams/run-inventory.py               # Export config audit
scripts/teams/run-inventory.ps1              # Windows version
scripts/graph/01-verify-setup.py             # Verify everything works

# Automation
scripts/setup/setup-github-aws-iam.sh        # AWS credentials
scripts/setup/setup-github-azure-spn.sh      # Azure credentials
```

---

## 💡 Pro Tips

1. **Keep inventory updated**: After major changes, run `python scripts/teams/run-inventory.py` and commit
2. **Use git history**: Check what changed: `git log -- inventory/teams-config-inventory.md`
3. **Compare environments**: Use prompts in `.github/prompts/compare-teams-config.prompt.md`
4. **Automate validation**: Add inventory to GitHub Actions for weekly audits
5. **Never commit secrets**: `.env.local` is in `.gitignore` — never commit it

---

## 🔗 Bootstrap Prompts Quick Links

For Copilot users: Copy these URLs to chat to have agent run the prompts

1. [`bootstrap-dev-env.prompt.md`](.github/prompts/bootstrap-dev-env.prompt.md) — Local setup
2. [`bootstrap-teams-config.prompt.md`](.github/prompts/bootstrap-teams-config.prompt.md) — Teams bot
3. [`bootstrap-azure-spn.prompt.md`](.github/prompts/bootstrap-azure-spn.prompt.md) — Azure
4. [`bootstrap-aws-iam.prompt.md`](.github/prompts/bootstrap-aws-iam.prompt.md) — AWS
5. [`bootstrap-gh-workflow-creds.prompt.md`](.github/prompts/bootstrap-gh-workflow-creds.prompt.md) — GitHub

---

## 📞 Getting Help

1. **Setup stuck?** → Check the appropriate bootstrap prompt
2. **Script error?** → See [`TEAMS_INVENTORY_SCRIPTS_REFERENCE.md`](./docs/TEAMS_INVENTORY_SCRIPTS_REFERENCE.md)
3. **Configuration drift?** → Run `python scripts/teams/run-inventory.py` and compare
4. **Can't reproduce?** → Check "How to Reproduce" in `inventory/teams-config-inventory.md`

---

**Bookmark this file!** Reference it for common tasks.

**Questions?** Check `docs/` directory for comprehensive guides.

---

_Last Updated: February 16, 2026_
