# Rawi Weekly Performance System

A Streamlit system for the Rawi team to upload and review weekly performance.

## Main workflow

- Open the app.
- Use the left team list.
- Press a team member name.
- That member's records open in the main table.
- Use the time filter to show Today, This Week, Last Week, This Month, All Time, or a Custom Range.
- Use Upload to add new weekly performance.
- Use Reports for team summaries.

## Table columns

The member table shows:

- Date
- Title
- URL
- WC / Word Count
- Status
- Files
- Updated

The Project column was removed.

## Upload fields

- Team member
- Date
- Status: Completed, In Process, Review, Edit
- Word Count
- Performance Title
- Details
- Source links
- Uploaded source files/images

## Team members

- Faten Aish
- Yazan Dmara
- Kamal Arslan
- Nour Aldeen
- Doha Alrefai
- Ali

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
