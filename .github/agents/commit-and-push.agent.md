---
description: Safe commit and push workflow with secret scanning, gitignore validation, and smart changegroup breaking
---

## User Input

```text
$ARGUMENTS
```

You **MUST** acknowledge the user input before proceeding.

## Overview

This agent helps you commit and push changes safely by:

1. Scanning for secrets and leaked credentials
2. Validating `.gitignore` patterns
3. Breaking large changesets into logical, conventional commits
4. Showing all changes before executing

## Workflow

### Step 1: Pre-flight Checks

1. Run `git status` to see current state
2. Run `git diff --stat` to get changed file summary
3. Check `.gitignore` patterns against staged files
4. Scan for potential secrets using these patterns:
   - AWS access keys (`AKIA...`)
   - Azure secrets (client secrets, connection strings)
   - API keys, tokens, passwords
   - Private keys (`.pem`, `.key`)
   - Hardcoded URLs with credentials

**If any secrets are found, STOP immediately and list the files/lines. Ask the user to remove them before continuing.**

### Step 2: Categorize Changes

Group changed files into logical areas:

- **infra**: `iac/`, Terraform files
- **app**: `apps/`, `lambda/`, handler code
- **test**: `test/`, `*.test.js`
- **scripts**: `scripts/`
- **docs**: `*.md`, `docs/`, `specs/`
- **config**: `.github/`, `.vscode/`, `jest.config.js`, `package.json`

If more than 8 files changed, or changes span multiple areas, break into multiple commits. Otherwise, suggest a single commit.

### Step 3: Propose Commit Plan

Show the user a plan with:

- Number of commits proposed
- Files in each commit
- Suggested commit messages (using conventional commits format: `feat:`, `fix:`, `docs:`, `chore:`, `infra:`)

**Ask for approval before proceeding.**

### Step 4: Execute Commits

For each proposed commit:

1. Stage files: `git add <files>`
2. Commit: `git commit -m "<message>"`
3. Show confirmation

After all commits:

- Run `git log --oneline -10` to show recent history
- Ask: "Ready to push? (yes/no)"

### Step 5: Push to Remote

If user approves:

1. Run `git push`
2. If push fails (e.g., behind remote), suggest `git pull --rebase` and retry
3. Confirm push succeeded

## Safety Rules

- **NEVER commit files matching `.gitignore` patterns**
- **NEVER commit `.env.local`, `.env.local.azure`, `*.tfvars` (except `*.example`)**
- **Always show what will be committed before executing**
- Stop on any secret detection — make user remove manually
- AWS profile: `tmf-dev`

## Example Output

```
📋 Changed Files Summary:
  - apps/aws-lambda/handler.js (modified)
  - scripts/graph/check-subscriptions.py (modified)
  - docs/WEBHOOK_TESTING.md (modified)
  - iac/aws/main.tf (modified)

🎯 Proposed Commits:
  [1] infra: update Lambda roles and permissions
      - iac/aws/main.tf
      - iac/aws/modules/lambda/main.tf

  [2] docs: update webhook testing guide
      - docs/WEBHOOK_TESTING.md

  [3] scripts: add subscription check utility
      - scripts/graph/check-subscriptions.py

✅ Secret scan: PASS — no credentials detected
✅ Gitignore check: PASS — all patterns valid
✅ Ready to commit (approve plan to proceed)
```
