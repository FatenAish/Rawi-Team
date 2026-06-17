# Rawi Team Performance

A Streamlit system for recording weekly performance for the Rawi team.

## Main flow

1. Open **Upload**.
2. Pick the team member name.
3. Pick the date.
4. Pick the status:
   - Completed
   - In Process
   - Upload
   - Review
5. Pick the project:
   - Summaries
   - Audio
   - Other tasks

## Dynamic fields

### Summaries
- Summary name
- Link
- WC

### Audio
- Summary name
- Link
- Duration

### Other tasks
- Details
- Upload file or image

## Records

Open **Team Details**, press a team member name on the left, and the records will show under that member with a date filter.

## Run locally on Windows

```bat
cd /d C:\Users\User\Desktop\Rawi-Team
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Important

For local testing, SQLite is used. For real shared team use on Streamlit Cloud, connect the app to Google Sheets or Supabase so records do not reset.
