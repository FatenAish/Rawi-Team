# Rawi Team Performance

A Streamlit system for the Rawi team to upload daily and weekly performance records and review them by team member.

## Main flow

1. Open **Upload**.
2. Pick the team member name.
3. Pick the status:
   - Completed
   - In Process
   - Upload
   - Review
4. Pick the project name:
   - Summaries
   - Audio
   - Other tasks
5. The fields change based on the project name:
   - **Summaries:** Summary Name, Link, WC, Date
   - **Audio:** Summary Name, Link, Duration, Date
   - **Other tasks:** Details, File/Image Upload, Date
6. Open **Team Details**.
7. Press the team member name on the left to see that member's records.
8. Use the date filter to view Today, This Week, Last Week, This Month, All Time or Custom Range.
9. Open any record to edit or delete it.

## Pages

- **Team Details:** Airtable-style member list and records table.
- **Upload:** Add a new performance record.
- **Reports:** Team reporting by date, member, status and project name.

## Table columns

The member record table shows:

- Date
- Title
- URL
- Status
- WC
- Duration
- Files
- Updated

The system does not show a Project column in the member record table, but the project name is saved and used for reports.

## Run locally on Windows

```bat
cd /d C:\Users\User\Desktop\Rawi-Team
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud deployment

Repository: `FatenAish/Rawi-Team`  
Branch: `main`  
Main file path: `app.py`

Important: SQLite is fine for local testing. For stable shared team use on Streamlit Cloud, connect the app to Google Sheets or Supabase later.
