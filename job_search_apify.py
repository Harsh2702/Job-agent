import os
import time
import smtplib
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from urllib.parse import quote_plus
from apify_client import ApifyClient

# -----------------------------------------------
# CONFIG - edit these to match your search
# -----------------------------------------------
KEYWORDS = ["Data Scientist", "Machine Learning Engineer", "AI Engineer"]
LOCATION = "Germany"

# These come from GitHub Secrets
APIFY_TOKEN        = os.environ["APIFY_TOKEN"]
GMAIL_USER         = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

# If RECIPIENT_EMAIL secret is not set, fall back to GMAIL_USER
_recipient = os.environ.get("RECIPIENT_EMAIL", "").strip()
RECIPIENT_EMAIL = _recipient if _recipient else GMAIL_USER

# -----------------------------------------------
# ACTOR IDs
# -----------------------------------------------
ACTORS = {
    "LinkedIn":  "curious_coder/linkedin-jobs-scraper",
    "Indeed":    "valig/indeed-jobs-scraper",
    "StepStone": "easyapi/stepstone-jobs-scraper",
    "Xing":      "shahidirfan/Xing-Jobs-Scraper",
}

# -----------------------------------------------
# BUILD LINKEDIN URL
# LinkedIn requires a full search URL, not raw keywords.
# f_TPR=r86400 = posted in last 24 hours (86400 seconds)
# -----------------------------------------------
def build_linkedin_url(keyword, location):
    kw  = quote_plus(keyword)
    loc = quote_plus(location)
    return f"https://www.linkedin.com/jobs/search/?keywords={kw}&location={loc}&f_TPR=r86400&position=1&pageNum=0"

# -----------------------------------------------
# ACTOR INPUTS - correct field names per schema
# -----------------------------------------------
def get_actor_input(platform, keyword, location):
    if platform == "LinkedIn":
        return {
            "urls":  [build_linkedin_url(keyword, location)],
            "count": 20,
        }
    elif platform == "Indeed":
        return {
            "title":      keyword,
            "location":   location,
            "country":    "de",         # Germany
            "limit":      20,
            "datePosted": "1",          # last 1 day
        }
    elif platform == "StepStone":
        return {
            "searchKeywords": keyword,
            "location":       location,
            "maxResults":     20,
        }
    elif platform == "Xing":
        return {
            "keyword":        keyword,  # note: singular, not "keywords"
            "location":       location,
            "results_wanted": 20,
        }

# -----------------------------------------------
# NORMALIZE raw fields to a common structure
# -----------------------------------------------
def normalize_job(raw, platform, keyword):
    job = {
        "Platform":    platform,
        "Keyword":     keyword,
        "Title":       None,
        "Company":     None,
        "Location":    None,
        "Posted At":   None,
        "Apply Link":  None,
        "Salary":      None,
        "Description": None,
    }

    if platform == "LinkedIn":
        job["Title"]       = raw.get("title") or raw.get("jobTitle")
        job["Company"]     = raw.get("company") or raw.get("companyName")
        job["Location"]    = raw.get("location") or raw.get("jobLocation")
        job["Posted At"]   = raw.get("postedAt") or raw.get("datePosted")
        job["Apply Link"]  = raw.get("jobUrl") or raw.get("url")
        job["Salary"]      = raw.get("salary")
        job["Description"] = raw.get("description") or raw.get("jobDescription")

    elif platform == "Indeed":
        job["Title"]       = raw.get("positionName") or raw.get("title")
        job["Company"]     = raw.get("company")
        job["Location"]    = raw.get("location")
        job["Posted At"]   = raw.get("postedAt") or raw.get("date")
        job["Apply Link"]  = raw.get("url") or raw.get("jobUrl")
        job["Salary"]      = raw.get("salary") or raw.get("salaryText")
        job["Description"] = raw.get("description") or raw.get("jobDescription")

    elif platform == "StepStone":
        job["Title"]       = raw.get("jobTitle") or raw.get("title")
        job["Company"]     = raw.get("companyName") or raw.get("company")
        job["Location"]    = raw.get("location") or raw.get("jobLocation")
        job["Posted At"]   = raw.get("postedAt") or raw.get("datePosted")
        job["Apply Link"]  = raw.get("jobUrl") or raw.get("url")
        job["Salary"]      = raw.get("salary") or raw.get("salaryRange")
        job["Description"] = raw.get("description")

    elif platform == "Xing":
        job["Title"]       = raw.get("title") or raw.get("jobTitle")
        job["Company"]     = raw.get("companyName") or raw.get("company")
        job["Location"]    = raw.get("location") or raw.get("city")
        job["Posted At"]   = raw.get("publishedAt") or raw.get("postedAt")
        job["Apply Link"]  = raw.get("url") or raw.get("jobUrl")
        job["Salary"]      = raw.get("salary")
        job["Description"] = raw.get("description")

    return job

# -----------------------------------------------
# FILTER - keep only jobs posted in last 24 hours
# -----------------------------------------------
def is_within_24h(posted_at_str):
    if not posted_at_str:
        return True

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(str(posted_at_str), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt >= cutoff
        except ValueError:
            continue

    return True

# -----------------------------------------------
# FETCH JOBS from all platforms and all keywords
# -----------------------------------------------
def fetch_all_jobs():
    client   = ApifyClient(APIFY_TOKEN)
    all_jobs = []

    for keyword in KEYWORDS:
        for platform, actor_id in ACTORS.items():
            print(f"Running {platform} for keyword: {keyword}")

            try:
                actor_input = get_actor_input(platform, keyword, LOCATION)
                run         = client.actor(actor_id).call(run_input=actor_input)
                time.sleep(2)

                dataset_id = run.get("defaultDatasetId")
                if not dataset_id:
                    print(f"  No dataset returned, skipping.")
                    continue

                items = list(client.dataset(dataset_id).iterate_items())
                print(f"  Got {len(items)} raw results")

                for raw in items:
                    job = normalize_job(raw, platform, keyword)
                    if is_within_24h(job["Posted At"]):
                        all_jobs.append(job)

            except Exception as e:
                print(f"  Error: {e}")
                continue

    if not all_jobs:
        return pd.DataFrame()

    df = pd.DataFrame(all_jobs)

    # some actors return dicts or lists inside fields - flatten everything to strings
    for col in df.columns:
        df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)

    df = df.drop_duplicates(subset=["Title", "Company", "Location"])
    df = df.reset_index(drop=True)

    # keep top 20 per platform across all keywords combined
    df = df.groupby("Platform", group_keys=False).head(20)
    df = df.reset_index(drop=True)

    df["Scraped At"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    return df

# -----------------------------------------------
# BUILD EXCEL FILE in memory
# -----------------------------------------------
def build_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Jobs")

        workbook  = writer.book
        worksheet = writer.sheets["Jobs"]

        from openpyxl.styles import Font, PatternFill, Alignment
        from openpyxl.utils import get_column_letter

        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)

        for col_num, col_name in enumerate(df.columns, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        for col_num, col_name in enumerate(df.columns, 1):
            col_values = df[col_name].fillna("").astype(str).apply(len)
            max_len = max(int(col_values.max()), len(col_name))
            col_letter = get_column_letter(col_num)
            worksheet.column_dimensions[col_letter].width = min(max_len + 4, 60)

    output.seek(0)
    return output

# -----------------------------------------------
# SEND EMAIL with Excel attachment
# -----------------------------------------------
def send_email(df, excel_bytes):
    today    = datetime.now().strftime("%Y-%m-%d")
    total    = len(df)
    platforms = df["Platform"].value_counts().to_dict()

    platform_summary = "\n".join([f"  - {k}: {v} jobs" for k, v in platforms.items()])

    body = f"""Hi,

Here are your daily job results for {today}.

Total jobs found: {total}

Breakdown by platform:
{platform_summary}

Keywords searched: {", ".join(KEYWORDS)}
Location: {LOCATION}

The full list with apply links is attached as an Excel file.

Good luck with your search!
"""

    msg = MIMEMultipart()
    msg["From"]    = GMAIL_USER
    msg["To"]      = RECIPIENT_EMAIL
    msg["Subject"] = f"Daily Jobs - {today} ({total} listings)"

    msg.attach(MIMEText(body, "plain"))

    part = MIMEBase("application", "octet-stream")
    part.set_payload(excel_bytes.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename=jobs_{today}.xlsx"
    )
    msg.attach(part)

    print(f"Sending email to: {RECIPIENT_EMAIL}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())

    print("Email sent successfully.")

# -----------------------------------------------
# MAIN
# -----------------------------------------------
if __name__ == "__main__":
    print(f"Starting daily job search - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Keywords: {KEYWORDS}")
    print(f"Location: {LOCATION}")
    print(f"Sending results to: {RECIPIENT_EMAIL}\n")

    df = fetch_all_jobs()

    if df.empty:
        print("No jobs found. Nothing to send.")
    else:
        print(f"\nTotal jobs found: {len(df)}")
        print(df["Platform"].value_counts().to_string())

        excel = build_excel(df)
        send_email(df, excel)

        print("Done!")
