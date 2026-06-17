# Rawi Weekly Performance Dashboard

A Streamlit system for the Rawi team to record weekly performance and review each member's work from a clickable team view.

## What changed

- Airtable-style data workspace.
- Left team list: press a team member name to show that member's performance.
- Time filter: Today, This Week, Last Week, This Month, All Time, or Custom Range.
- Main table with Date, Project, Title, URL, Status, Files and Updated time.
- Upload page for performance records.
- Source links and source file/image uploads.
- Record details with edit and delete actions.
- Reports page with team summaries and CSV export.
- SQLite database with migration support for older records.

## Team members

- Faten Aish
- Yazan Dmara
- Kamal Arslan
- Nour Aldeen
- Doha Alrefai
- Ali

## Status options

- Completed
- In Process
- Review
- Edit

## Run on Windows

```bat
cd /d C:\Users\User\Desktop\Rawi-Team
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Notes

The system saves records in `rawi_performance.db` and uploaded files in the `uploads` folder.

For real shared team use, run the app from one hosted/shared server. If each person runs it separately on their own laptop, each person will have a separate local database.
