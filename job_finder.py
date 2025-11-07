#!/usr/bin/env python3
import os, requests
from datetime import datetime, timezone

# ---- config ----
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
BING_API_KEY = os.getenv("BING_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
MAX_RESULTS = 10

COMPANY_DOMAINS = [
    "google.com","amazon.com","microsoft.com","meta.com","apple.com",
    "netflix.com","github.com","stripe.com","palantir.com","wellfound.io",
    "linkedin.com","indeed.com","airbnb.com","uber.com"
]

KEYWORDS = [
    '"software engineer" "hiring"','"software developer" "hiring"',
    '"full stack engineer" "job"','"backend engineer" "job"'
]

def bing_search(q):
    url = "https://api.bing.microsoft.com/v7.0/search"
    r = requests.get(url,
        headers={"Ocp-Apim-Subscription-Key": BING_API_KEY},
        params={"q": q, "count": MAX_RESULTS, "responseFilter": "Webpages"},
        timeout=20)
    r.raise_for_status()
    return [
        {"title": v["name"], "url": v["url"]}
        for v in r.json().get("webPages", {}).get("value", [])
    ]

def serpapi_search(q):
    url = "https://serpapi.com/search.json"
    r = requests.get(url,
        params={"engine":"google","q":q,"api_key":SERPAPI_KEY,"num":MAX_RESULTS},
        timeout=20)
    r.raise_for_status()
    return [{"title":v["title"],"url":v["link"]} for v in r.json().get("organic_results",[])]

def get_jobs():
    seen, jobs = set(), []
    for kw in KEYWORDS:
        q = f'{kw} site:careers OR site:jobs OR site:linkedin.com/jobs OR site:wellfound.io'
        try:
            results = bing_search(q) if BING_API_KEY else serpapi_search(q)
        except Exception as e:
            print("Search error:", e)
            results = []
        for r in results:
            if r["url"] not in seen:
                seen.add(r["url"])
                jobs.append(r)
    jobs.sort(key=lambda x: 0 if any(d in x["url"] for d in COMPANY_DOMAINS) else 1)
    return jobs

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True})

if __name__ == "__main__":
    jobs = get_jobs()
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    if not jobs:
        msg = f"📰 {now}\nNo new jobs found today."
    else:
        msg = f"📰 Daily Developer Jobs ({now})\n\n"
        for i, j in enumerate(jobs[:15], 1):
            msg += f"{i}. {j['title']}\n{j['url']}\n\n"
    send_telegram(msg[:4000])  # Telegram limit
