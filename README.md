# Spend Review

A small Streamlit app that reads an HDFC Bank account statement (`.xls` / `.xlsx`)
and groups the transactions into spending categories.

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

## Notes

No data is stored. Uploads are held in memory for the duration of the session only.
Statement files are gitignored and should never be committed.

### Privacy

- Uploaded statements are parsed in memory and never written to disk.
- Parsing is intentionally uncached, so no statement data persists in server
  memory between sessions.
- Streamlit usage telemetry is disabled in `.streamlit/config.toml`.
