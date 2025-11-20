# Scheduled Trading Setup Guide

This application uses GitHub Actions to trigger trading tasks at specific times, eliminating the need for Heroku worker/beat dynos and saving costs.

## Architecture

- **Web Dyno**: Runs the Flask application with API endpoints
- **GitHub Actions**: Free cron scheduler that calls API endpoints at scheduled times
- **No Worker/Beat Dynos**: Saves $25-50/month on Heroku costs

## Setup Instructions

### 1. Generate a Secure API Key

Generate a secure API key for the scheduler:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Configure Heroku Environment Variables

Set the scheduler API key and app URL in Heroku:

```bash
# Set the API key
heroku config:set SCHEDULER_API_KEY=your-secure-api-key-here --app <app_name>

# Verify it's set
heroku config:get SCHEDULER_API_KEY --app <app_name>
```

### 3. Configure GitHub Secrets

1. Go to your GitHub repository: https://github.com/yourusername/vibe-stock-market-predictor
2. Navigate to **Settings → Secrets and variables → Actions**
3. Add the following secrets:
   - **SCHEDULER_API_KEY**: The same API key you set in Heroku
   - **HEROKU_APP_URL**: `https://<app_name>-7f8911888071.herokuapp.com`

### 4. Enable GitHub Actions

1. Go to the **Actions** tab in your GitHub repository
2. If workflows are disabled, click **"I understand my workflows, go ahead and enable them"**
3. You should see the following workflows:
   - NYSE Trading Sessions
   - LSE Trading Sessions
   - TSE Trading Sessions
   - Portfolio Health Check

### 5. Test the Setup

#### Test via GitHub Actions UI

1. Go to **Actions** → Select a workflow (e.g., "NYSE Trading Sessions")
2. Click **"Run workflow"** dropdown
3. Select the branch and trading session
4. Click **"Run workflow"**
5. Monitor the execution to ensure it completes successfully

#### Test via curl (from your terminal)

```bash
# Set your API key and app URL
API_KEY="your-secure-api-key-here"
APP_URL="https://<app_name>-7f8911888071.herokuapp.com"

# Test NYSE morning trading
curl -X POST "$APP_URL/api/scheduled/execute-trades" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"timezone": "America/New_York", "time_of_day": "morning"}' \
  | jq '.'

# Test portfolio health check
curl -X POST "$APP_URL/api/scheduled/portfolio-health-check" \
  -H "X-API-Key: $API_KEY" \
  | jq '.'

# Test health endpoint (no auth required)
curl "$APP_URL/api/scheduled/health" | jq '.'
```

## Trading Schedules

### NYSE (America/New_York)
- **Morning Session**: 10:00 AM EST (7:00 AM PST) - `15:00 UTC Mon-Fri`
- **Midday Session**: 12:30 PM EST (9:30 AM PST) - `17:30 UTC Mon-Fri`
- **Afternoon Session**: 3:00 PM EST (12:00 PM PST) - `20:00 UTC Mon-Fri`

### LSE (Europe/London)
- **Morning Session**: 8:30 AM GMT - `08:30 UTC Mon-Fri`
- **Midday Session**: 12:00 PM GMT - `12:00 UTC Mon-Fri`
- **Afternoon Session**: 3:30 PM GMT - `15:30 UTC Mon-Fri`

### TSE (Asia/Tokyo)
- **Morning Session**: 9:30 AM JST - `00:30 UTC Mon-Fri`
- **Afternoon Session**: 1:00 PM JST - `04:00 UTC Mon-Fri`
- **Closing Session**: 2:30 PM JST - `05:30 UTC Mon-Fri`

### Portfolio Health Check
- **Daily Check**: 4:30 PM EST (after NYSE close) - `21:30 UTC Mon-Fri`

## Monitoring

### View Workflow Execution Logs

1. Go to **Actions** tab in GitHub
2. Click on a workflow run to see detailed logs
3. Check for any errors or failed API calls

### View Application Logs

```bash
# View Heroku logs
heroku logs --tail --app <app_name>

# Filter for scheduled task logs
heroku logs --tail --app <app_name> | grep "Scheduled"
```

### Check Trader Activity

Visit your app and go to the **Machine Traders** tab to see:
- Recent trades executed by scheduled tasks
- Trader performance and P/L
- Last trade timestamp

## Troubleshooting

### Workflow fails with "Unauthorized"
- Verify `SCHEDULER_API_KEY` is set correctly in both Heroku and GitHub Secrets
- Ensure they match exactly (copy-paste to avoid typos)

### Workflow fails with "Connection refused" or 404
- Verify `HEROKU_APP_URL` is set correctly in GitHub Secrets
- Check that your Heroku app is running: `heroku ps --app <app_name>`
- Test the health endpoint: `curl https://your-app.herokuapp.com/api/scheduled/health`

### No trades are executing
- Check that you have active traders with the correct timezone
- View logs: `heroku logs --tail --app <app_name> | grep "Trading"`
- Manually trigger a workflow to test

### Workflow runs but no changes in database
- Check application logs for errors during task execution
- Verify Alpha Vantage API key is set and working
- Ensure traders are in `active` status

## Cost Savings

### Before (with Celery workers)
- Web dyno: $7/month
- Worker dyno: $7/month
- Beat dyno: $7/month (or combined with worker)
- Redis addon: $0-5/month
- **Total: ~$21-26/month**

### After (with GitHub Actions)
- Web dyno: $7/month
- GitHub Actions: $0/month (2000 minutes free)
- **Total: ~$7/month**

**Savings: ~$14-19/month (66-73% reduction)**

## Alternative Schedulers

If you prefer not to use GitHub Actions, you can also use:

### 1. Heroku Scheduler (Free Add-on)
```bash
heroku addons:create scheduler:standard --app <app_name>
```

Then add tasks in the Heroku Dashboard:
```bash
# Every hour at :00
curl -X POST https://your-app.herokuapp.com/api/scheduled/execute-trades \
  -H "X-API-Key: $SCHEDULER_API_KEY" \
  -d '{"timezone": "America/New_York", "time_of_day": "morning"}'
```

### 2. Cron-job.org (Free)
- Create a free account at https://cron-job.org
- Add your API endpoints with the X-API-Key header
- Configure schedules

### 3. EasyCron (Free tier available)
- Visit https://www.easycron.com
- Set up cron jobs with custom headers

## Security Notes

- **Never commit** `SCHEDULER_API_KEY` to the repository
- Keep it in Heroku config vars and GitHub Secrets only
- Rotate the API key periodically for security
- Monitor for unauthorized access attempts in logs
