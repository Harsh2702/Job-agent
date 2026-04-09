# Daily Job Search - Setup Guide

## What you will have after this setup

A script that runs every morning (Mon-Sat) at 7am CEST, searches for Data Scientist,
Machine Learning Engineer, and AI Engineer jobs in Germany, and emails you an Excel
file with all listings and apply links.

---

## Step 1 - Create a GitHub repository

1. Go to github.com and sign in (or create a free account)
2. Click the "+" icon at the top right and select "New repository"
3. Name it: `job-search-agent`
4. Keep it Private
5. Click "Create repository"

---

## Step 2 - Upload the files

Upload these 3 files to your repository in this exact folder structure:

```
job-search-agent/
  job_search.py
  requirements.txt
  .github/
    workflows/
      job_search.yml
```

To do this on GitHub:
1. Click "Add file" > "Upload files" for job_search.py and requirements.txt
2. For the workflow file, click "Add file" > "Create new file"
   - Type the path: `.github/workflows/job_search.yml`
   - Paste the contents of job_search.yml

---

## Step 3 - Add your secret keys (do not skip this)

Your API keys must never be in the code. They go in GitHub Secrets.

1. In your repository, go to "Settings" (top menu)
2. In the left sidebar click "Secrets and variables" > "Actions"
3. Click "New repository secret" and add these 3 secrets one by one:

| Secret Name       | Value                                      |
|-------------------|--------------------------------------------|
| RAPIDAPI_KEY      | Your JSearch API key from RapidAPI         |
| GMAIL_USER        | harshjoshi.3077@gmail.com                  |
| GMAIL_APP_PASSWORD| Your 16-character Gmail App Password       |

---

## Step 4 - Get your JSearch API key

1. Go to rapidapi.com and create a free account
2. Search for "JSearch" in the marketplace
3. Subscribe to the Free plan (100 requests/month - enough for you)
4. Go to the JSearch API page and copy your "X-RapidAPI-Key"
5. Paste it as the RAPIDAPI_KEY secret in Step 3

---

## Step 5 - Get your Gmail App Password

You need this so the script can send emails automatically.

1. Go to myaccount.google.com
2. Make sure 2-Step Verification is turned ON (required)
   - If not, go to "Security" and enable it first
3. Search "App Passwords" in the search bar at the top
4. Click "App Passwords"
5. In the dropdown, select "Mail" and click "Generate"
6. Copy the 16-character code (spaces do not matter)
7. Paste it as the GMAIL_APP_PASSWORD secret in Step 3

---

## Step 6 - Test it manually

Before waiting until tomorrow morning, trigger it manually to make sure it works.

1. In your repository, click the "Actions" tab
2. Click "Daily Job Search" in the left sidebar
3. Click "Run workflow" > "Run workflow"
4. Wait 30-60 seconds
5. Check your email - you should receive the Excel file

If it fails, click on the failed run to see the error logs.

---

## How to change keywords or location later

Open `job_search.py` and find these lines near the top:

```python
KEYWORDS = ["Data Scientist", "Machine Learning Engineer", "AI Engineer"]
LOCATION = "Germany"
```

Edit them and push the changes to GitHub. The next run will use the new values.

---

## How to change the schedule

Open `.github/workflows/job_search.yml` and find this line:

```yaml
- cron: '0 5 * * 1-6'
```

This means: 5am UTC (7am CEST), Monday to Saturday.

To change the time, adjust the hour (0 5 = 5am UTC).
For 8am CEST change to: `0 6 * * 1-6`

---

## Troubleshooting

**No email received:**
- Check the Actions tab in GitHub for errors
- Make sure Gmail App Password is correct
- Make sure 2-Step Verification is enabled on your Google account

**API errors:**
- Check your RAPIDAPI_KEY secret is correct
- Check you are subscribed to JSearch on RapidAPI

**Jobs look outdated:**
- JSearch's "today" filter depends on when companies post jobs
- Some listings may show as today even if posted yesterday
