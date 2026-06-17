# Rawi Weekly Performance Dashboard

A Streamlit system for the Rawi team to record weekly performance.

## Features

- Weekly performance upload form
- Fixed team member list
- Status options: Completed, In Process, Review, Edit
- Source links support
- Image and file uploads
- Overview dashboard with KPI cards
- Team snapshot
- Weekly records table
- Records page with filters, edit, delete and CSV export
- Reports page with weekly summaries
- Local SQLite database

## Team members

- Faten Aish
- Yazan Dmara
- Kamal Arslan
- Nour Aldeen
- Doha Alrefai
- Ali

## Run on Windows

```bat
cd /d C:\Users\User\Desktop\rawi_streamlit_system
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Notes

The system saves records in `rawi_performance.db` and uploaded files in the `uploads` folder. For shared team use, run the app from one hosted/shared machine so everyone writes to the same database.
