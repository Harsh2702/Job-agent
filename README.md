# Daily Job Digest

An automated job search pipeline that runs every morning via GitHub Actions. It scrapes LinkedIn, Indeed, StepStone, and Xing for fresh listings using Apify actors, deduplicates the results, and emails you a formatted Excel report before you start your day — no browser needed.

Built for job seekers targeting Data Science / ML / AI roles in Germany, but fully configurable for any keywords or location.

---

## How it works

```
GitHub Actions (cron: Mon–Sat 7am CEST)
        │
        ▼
job_search_apify.py
        │
        ├── Apify Actor: LinkedIn Jobs Scraper
        ├── Apify Actor: Indeed Jobs Scraper
        ├── Apify Actor: StepStone Jobs Scraper
        └── Apify Actor: Xing Jobs Scraper
                │
                ▼
        Deduplicate + filter last 24h
                │
                ▼
        Build formatted Excel (.xlsx)
        with clickable Apply links
                │
                ▼
        Gmail SMTP → Your inbox
```

Each run searches all configured keywords × all platforms, keeps only listings posted in the last 24 hours, deduplicates by title + company + location, and sends one Excel file capped at 20 results per platform.

---

## Setup Guide

### Step 1 - Create a GitHub repository

1. Go to github.com and sign in (or create a free account)
2. Click the "+" icon at the top right and select "New repository"
3. Name it: `job-search-agent`
4. Keep it Private
5. Click "Create repository"

---

### Step 2 - Upload the files

Upload these files to your repository in this exact folder structure:

```
job-search-agent/
  job_search_apify.py
  requirements.txt
  .github/
    workflows/
      job_search_apify.yml
```

To do this on GitHub:
1. Click "Add file" > "Upload files" for `job_search_apify.py` and `requirements.txt`
2. For the workflow file, click "Add file" > "Create new file"
   - Type the path: `.github/workflows/job_search_apify.yml`
   - Paste the contents of `job_search_apify.yml`

---

### Step 3 - Add your secret keys (do not skip this)

Your API keys must never be in the code. They go in GitHub Secrets.

1. In your repository, go to "Settings" (top menu)
2. In the left sidebar click "Secrets and variables" > "Actions"
3. Click "New repository secret" and add these secrets one by one:

| Secret Name        | Value                                              |
|--------------------|----------------------------------------------------|
| `APIFY_TOKEN`      | Your Apify API token (from apify.com/account)      |
| `GMAIL_USER`       | Your Gmail address                                 |
| `GMAIL_APP_PASSWORD` | Your 16-character Gmail App Password             |
| `RECIPIENT_EMAIL`  | Email to receive the report (can be same as above) |

---

### Step 4 - Get your Apify token

1. Go to [apify.com](https://apify.com) and create a free account
2. Go to **Settings → Integrations** and copy your **API token**
3. Paste it as the `APIFY_TOKEN` secret in Step 3

The free Apify plan includes $5/month of compute — enough for daily runs.

---

### Step 5 - Get your Gmail App Password

You need this so the script can send emails automatically.

1. Go to myaccount.google.com
2. Make sure 2-Step Verification is turned ON (required)
   - If not, go to "Security" and enable it first
3. Search "App Passwords" in the search bar at the top
4. Click "App Passwords"
5. In the dropdown, select "Mail" and click "Generate"
6. Copy the 16-character code (spaces do not matter)
7. Paste it as the `GMAIL_APP_PASSWORD` secret in Step 3

---

### Step 6 - Enable the schedule

Open `.github/workflows/job_search_apify.yml` and uncomment the schedule lines:

```yaml
on:
  schedule:
    - cron: '0 5 * * 1-6'   # 5am UTC = 7am CEST, Monday to Saturday
  workflow_dispatch:
```

Commit and push. The pipeline will now run automatically every weekday morning.

---

### Step 7 - Test it manually

Before waiting until tomorrow morning, trigger it manually to make sure it works.

1. In your repository, click the "Actions" tab
2. Click "Daily Job Search Apify" in the left sidebar
3. Click "Run workflow" > "Run workflow"
4. Wait 60–90 seconds
5. Check your email — you should receive the Excel file

If it fails, click on the failed run to see the error logs.

---

## Customise keywords or location

Open `job_search_apify.py` and edit these lines near the top:

```python
KEYWORDS = ["Data Scientist", "Machine Learning Engineer", "AI Engineer"]
LOCATION = "Germany"
```

Push the change. The next run will use the new values.

---

## Change the schedule

Open `.github/workflows/job_search_apify.yml` and adjust the cron expression:

```yaml
- cron: '0 5 * * 1-6'
```

This means: 5am UTC (7am CEST), Monday to Saturday.
For 8am CEST change to: `0 6 * * 1-6`

---

## Troubleshooting

**No email received:**
- Check the Actions tab in GitHub for errors
- Make sure Gmail App Password is correct
- Make sure 2-Step Verification is enabled on your Google account

**Apify errors:**
- Check your `APIFY_TOKEN` secret is correct and the account is active
- Check your Apify usage limit hasn't been exceeded for the month

**Jobs look outdated:**
- The 24-hour filter depends on when platforms timestamp their listings
- Some listings may appear slightly outside the window depending on timezone handling
