# GitHub Issues for Missing Workflows

## Issue 1: Add Scheduled Maintenance Workflow

**Title:** [Workflow] Scheduled maintenance — check webhook subscriptions & renew

**Description:**

Add a scheduled GitHub Actions workflow that runs nightly to:

1. Check all webhook subscriptions for expiration (Graph API)
2. Alert if subscriptions expire within 24 hours
3. Optionally auto-renew subscriptions that are about to expire
4. Generate a maintenance report

**Acceptance Criteria:**

- [ ] Workflow runs on schedule (nightly at 2 AM UTC)
- [ ] Exports subscription list with expiration times
- [ ] Sends alert (email/Slack) if subscriptions expiring soon
- [ ] Logs results to GitHub Actions
- [ ] Can be manually triggered for testing
- [ ] No impact on running deployments

**Related Files:**

- `scripts/graph/check-subscriptions.py`
- `scripts/graph/list-subscriptions.py`

**Labels:** enhancement, workflow, maintenance

---

## Issue 2: Add Environment Sync Validation Workflow

**Title:** [Workflow] Environment sync — detect & alert on configuration drift

**Description:**

Add a scheduled GitHub Actions workflow that validates environment consistency across dev/staging/prod:

1. Compare Terraform outputs (app IDs, endpoints, etc.)
2. Check `.env.local` files are in sync (without exposing secrets)
3. Validate webhook URLs match deployed endpoints
4. Alert on drift or inconsistencies

**Acceptance Criteria:**

- [ ] Runs on schedule (daily at 8 AM UTC)
- [ ] Compares Terraform outputs across environments
- [ ] Validates webhook URL consistency
- [ ] Generates drift report
- [ ] Sends alerts to team (email/Slack/GitHub)
- [ ] Never exposes secrets in logs or reports
- [ ] Can be manually triggered for testing

**Related Files:**

- `iac/aws/outputs.tf`
- `iac/azure/outputs.tf`
- `scripts/compare-teams-config.prompt.md`

**Labels:** enhancement, workflow, monitoring

---

## How to Create Issues

Option 1: Use GitHub CLI

```bash
gh issue create --title "[Workflow] Scheduled maintenance — check webhook subscriptions & renew" \
  --body "$(cat .github/workflows/WORKFLOW_IDEAS.md | grep -A 20 'Issue 1:')" \
  --label "enhancement,workflow,maintenance"
```

Option 2: Create manually in GitHub UI

- Go to Issues tab
- Click "New issue"
- Copy title and description from above
