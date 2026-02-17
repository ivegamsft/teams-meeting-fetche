# Clean Up Teams App — Manifests, Test Data, Artifacts

## Purpose

Clean up the Teams app codebase and test artifacts: remove old manifests, delete test data, reset configs, and prepare for fresh deployment.

## Instructions

### Step 1: Audit App State

Review the current app structure:

```bash
ls -la teams-app/
cat teams-app/manifest.json
cat teams-app/manifest-dev.json
```

Check what exists:

- **manifest.json** — Production manifest
- **manifest-dev.json** — Development manifest
- Icon files (color.png, outline.png)
- localization files (if any)

### Step 2: Clean Up Old/Test Manifests

Identify manifests that are no longer needed:

1. **Old versions** (e.g., `manifest-v1.json`, `manifest-old.json`)
   - If found, delete them: `rm teams-app/manifest-*.bak`

2. **Development manifest** (`manifest-dev.json`)
   - Ask: Should this exist for local dev, or should `manifest.json` be used for all environments?
   - If keeping: ensure it points to the correct dev webhook URL
   - If removing: delete and use environment-based templating instead

3. **Environment-specific copies** (e.g., `manifest-prod.json`, `manifest-staging.json`)
   - If found, consolidate into a single manifest with templated values

### Step 3: Validate Active Manifests

For manifests being kept, validate the content:

```bash
# Check manifest syntax (if a validator exists)
npm run validate:manifests  # (if this script exists)
```

Or manually:

- `id` must be a valid UUID matching the Azure AD app registration
- `name.short` and `name.full` are correct
- `description` is accurate
- `developer.name` and `developer.websiteUrl` are set
- `validDomains` includes the correct webhook domain
- `bots[0].botId` matches `BOT_APP_ID`
- `composeExtensions` are configured (if used)
- `permissions` are minimal and necessary

### Step 4: Reset Manifest to Defaults

If manifests are outdated or have test values:

1. Regenerate from the example/template:

   ```bash
   cp teams-app/manifest-template.json teams-app/manifest.json
   ```

   (Or a similar example if it exists)

2. Update placeholders:
   - `<APP_ID>` → `$GRAPH_CLIENT_ID`
   - `<BOT_APP_ID>` → `$BOT_APP_ID`
   - `<WEBHOOK_URL>` → `$AWS_WEBHOOK_ENDPOINT` (AWS) or `$AZURE_WEBHOOK_ENDPOINT`
   - `<TENANT_ID>` → `$GRAPH_TENANT_ID`

3. Run a script to inject these values (if one exists):
   ```powershell
   powershell -File scripts/package-teams-app.ps1
   ```

### Step 5: Remove Test/Build Artifacts

Clean up temporary files from development:

```bash
# Remove dist output
rm -rf teams-app/dist/

# Remove node_modules if present
rm -rf teams-app/node_modules/

# Remove any .zip files
rm -f teams-app/*.zip
rm -f teams-meeting-fetcher-*.zip

# Remove test data or placeholder files
rm -f teams-app/test-*.json
rm -f teams-app/*.bak
```

### Step 6: Verify Manifest Integrity

Before committing:

```bash
# Check the manifest is valid JSON
jq . teams-app/manifest.json > /dev/null 2>&1 && echo "manifest.json: valid" || echo "manifest.json: INVALID"

jq . teams-app/manifest-dev.json > /dev/null 2>&1 && echo "manifest-dev.json: valid" || echo "manifest-dev.json: INVALID"
```

### Step 7: Document App Registration Changes

If the Teams app registration changed (new ID, new webhook, new bot):

1. Update the manifest version: `"version": "1.0.x"` → `"version": "1.0.(x+1)"`
2. Add a note in the manifest (as a comment or separate CHANGELOG entry):
   ```markdown
   ## Version 1.0.x Changes

   - Updated webhook URL to new deployment
   - Updated bot registration ID
   - Removed deprecated compose extensions
   ```

### Step 8: Commit Changes

If clean-up involved deletions or restructuring:

```bash
git add teams-app/
git commit -m "chore(teams-app): clean up old manifests and test artifacts"
```

Or let the "commit-and-push" prompt handle it.

### Rules

- **Never delete** the active manifest without having a replacement ready.
- Keep both `manifest.json` (prod) and `manifest-dev.json` (dev) if they differ in webhook URL.
- The manifest `id` MUST match the Azure AD app registration — do not change without updating the app.
- The `botId` MUST match `BOT_APP_ID` from your env — verify before committing.
- Always validate JSON syntax before committing.
