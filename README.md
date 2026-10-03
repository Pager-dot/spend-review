# Spend Review

A small Streamlit app that reads an HDFC Bank account statement (`.xls` / `.xlsx`)
and groups the transactions into spending categories.

**Live demo: https://spend-review.onrender.com** — free tier, so the first load
takes about a minute while the service wakes up. Nothing you upload is stored.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then upload your statement in the browser.

## What it shows

- Total spent, total received, transaction count
- Spend by category, with each category's share
- Top payees
- A filterable transaction table, downloadable as CSV

## Categories

Categorisation is keyword matching on the transaction narration. The rules live in
the `RULES` dict at the top of `app.py` — add keywords there to tune it.

Person-to-person UPI transfers fall into a single `Transfers to People` bucket,
since those narrations carry only a name and no merchant information.

## Privacy

- Uploaded statements are parsed in memory and never written to disk.
- Parsing is intentionally uncached, so no statement data persists in server
  memory between sessions.
- Streamlit usage telemetry is disabled in `.streamlit/config.toml`.

## Why open innovation matters here

This project deliberately uses **no API and no model**. The default way to categorise
transactions is to send each narration string to a hosted enrichment or LLM endpoint —
fewer lines than the rules in `app.py`, and it would mean every merchant, amount and
date in your statement leaves your machine in exchange for a one-word label. A closed
API gives you no way to opt out of that; there is no flag for "do the work locally".

Open tooling is what made the alternative viable:

- **The privacy claim is checkable, not promised.** Python, pandas, Streamlit and
  `xlrd` are open source and the app is one 200-line file. Read it, grep it for network
  calls, find none. A vendor's claim to have discarded your statement is unauditable.
- **The categories are a dict, not a black box.** When it mislabels your local kirana,
  that's a one-line edit in `RULES` — permanent and yours — not a support ticket.
- **No key, no quota, nothing to revoke.** `pip install -r requirements.txt` and it
  runs, offline, today or in five years.

**The honest cost:** person-to-person UPI transfers (44% of spend in my own test
statement) stay in one undifferentiated bucket. A large model with context about your
contacts might separate rent from splitting dinner; keyword rules cannot. That
information isn't in the statement, and the only way to get it would be to send the
statement somewhere. That trade wasn't worth making.
