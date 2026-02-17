# Commit & Push — Safe Check-in Assistant

## Purpose

Help me commit and push changes safely by auditing for secrets, validating `.gitignore`, and breaking large changesets into logical commits.

## Instructions

### Step 1: Pre-flight Checks

1. Run `git status` and `git diff --stat` to see what has changed.
2. Verify `.gitignore` covers all sensitive patterns. Cross-check against these known patterns in this project:
   - `.env`, `.env.local`, `.env.local.azure`, `*.tfvars`, `*.tfstate*`
   - `*.pem`, `*.key`, `*secret*`, `*credentials*`, `*api_key*`, `*access_token*`
   - `node_modules/`, `.terraform/`, `__pycache__/`, `.venv/`, `coverage/`
3. If any new file types or directories are staged that look sensitive but aren't in `.gitignore`, **stop and warn me** before continuing.

### Step 2: Secret Scanning

Scan all staged/changed files for potential secrets or credentials:

```
git diff --cached --name-only
git diff --name-only
```

For each changed file, search for patterns like:

- API keys, tokens, passwords, connection strings
- AWS access keys (`AKIA...`), Azure client secrets, tenant IDs that aren't variable references
- Hardcoded URLs with embedded credentials
- Private keys or certificate content

If anything suspicious is found, **list the file and line** and ask me to confirm before proceeding.

### Step 3: Break Down Large Changesets

If more than **8 files** have changed, or changes span multiple concerns (infra, app code, tests, docs):

1. Group changes into logical commits by area:
   - **infra**: `iac/`, Terraform files
   - **app**: `apps/`, `lambda/`, handler code
   - **test**: `test/`, `*.test.js`
   - **scripts**: `scripts/`
   - **docs**: `*.md`, `docs/`, `specs/`
   - **config**: `.github/`, `.vscode/`, `jest.config.js`, `package.json`
2. Propose a commit plan with suggested messages following conventional commits format (e.g., `feat:`, `fix:`, `docs:`, `chore:`, `infra:`)
3. Ask me to approve the plan before executing.

### Step 4: Commit & Push

For each logical group:

1. Stage the files: `git add <files>`
2. Commit with a clear message
3. After all commits, run `git log --oneline -10` to review
4. Push: `git push`

If the push fails (e.g., behind remote), suggest `git pull --rebase` and re-push.

### Rules

- **NEVER** commit files matching `.gitignore` patterns.
- **NEVER** commit `.env.local`, `.env.local.azure`, `*.tfvars` (only `*.tfvars.example` is allowed).
- The AWS profile for this project is `tmf-dev`.
- Always show me what will be committed before executing.
