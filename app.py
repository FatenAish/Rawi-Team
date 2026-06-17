import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import io

# --- 1. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('rawi_team.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS performance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member TEXT NOT NULL,
            task_date DATE NOT NULL,
            status TEXT NOT NULL,
            project TEXT NOT NULL,
            title TEXT NOT NULL,
            link TEXT,
            word_count INTEGER,
            duration TEXT,
            details TEXT
        )
    ''')
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect('rawi_team.db')
    df = pd.read_sql_query("SELECT * FROM performance_records", conn)
    conn.close()
    if not df.empty:
        df['task_date'] = pd.to_datetime(df['task_date']).dt.date
    return df

# --- 2. HELPER FUNCTIONS ---
def parse_duration_to_minutes(duration_str):
    # Dummy function for duration parsing - adjust to your logic
    try:
        if not duration_str or duration_str == "None":
            return 0
        parts = str(duration_str).split(':')
        return int(parts[0]) * 60 + int(parts[1]) if len(parts) > 1 else int(parts[0])
    except:
        return 0

def format_duration(minutes):
    return f"{minutes // 60}:{minutes % 60:02d}"

def apply_date_filter(df, date_filter, start_date=None, end_date=None):
    if df.empty: return df
    today = date.today()
    if date_filter == "Today":
        return df[df['task_date'] == today]
    elif date_filter == "This Week":
        start = today - timedelta(days=today.weekday())
        return df[df['task_date'] >= start]
    elif date_filter == "Custom Range" and start_date and end_date:
        return df[(df['task_date'] >= start_date) & (df['task_date'] <= end_date)]
    return df

def display_stat_cards(df):
    if df.empty:
        st.write("No data to display.")
        return
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("RECORDS", len(df))
    with c2: st.metric("COMPLETED", len(df[df['status'] == 'Completed']))
    with c3: st.metric("SUMMARIES", len(df[df['project'] == 'Summaries']))
    with c4: st.metric("TOTAL WORD COUNT", df['word_count'].sum())
    with c5: st.metric("FILES", 0) # Placeholder based on screenshots

# --- 3. PAGE LOGIC ---
def upload_page():
    st.header("Upload task")
    st.write("Record a new task for a team member")
    
    with st.form("upload_form"):
        c1, c2 = st.columns(2)
        with c1:
            member = st.selectbox("TEAM MEMBER", ["Select member...", "Faten Aish", "Yazan Dmara", "Kamal Arslan", "Nour Aldeen", "Doha Alrefai", "Ali"])
            status = st.selectbox("STATUS", ["Select status...", "Uploaded", "Completed", "In Progress"])
        with c2:
            task_date = st.date_input("DATE", value=date.today())
            project = st.selectbox("PROJECT", ["Select project...", "Summaries", "Audio", "Other Tasks"])
        
        st.markdown("---")
        
        if project == "Summaries":
            c3, c4 = st.columns([3, 1])
            with c3: title = st.text_input("TITLE")
            with c4: word_count = st.number_input("WORD COUNT", min_value=0, step=1)
            link = st.text_input("LINK")
            duration = None
        elif project == "Audio":
            c3, c4 = st.columns([3, 1])
            with c3: title = st.text_input("TITLE")
            with c4: duration = st.text_input("DURATION (MM:SS)")
            link = st.text_input("LINK")
            word_count = None
        else:
            st.info("Select a project type above to see task fields.")
            title, link, word_count, duration = "", "", None, None

        submitted = st.form_submit_button("Save task")
        
        if submitted:
            if member == "Select member..." or project == "Select project..." or not title:
                st.error("Please fill in all required fields (Member, Project, and Title).")
            else:
                conn = sqlite3.connect('rawi_team.db')
                c = conn.cursor()
                c.execute('''
                    INSERT INTO performance_records (member, task_date, status, project, title, link, word_count, duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (member, task_date, status, project, title, link, word_count, duration))
                conn.commit()
                conn.close()
                st.success("Task saved successfully!")

def team_details_page(df: pd.DataFrame) -> None:
    st.markdown("<div class='page-title'>Team details</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='page-subtitle'>Performance records for <b>{st.session_state.get('selected_member', 'the team')}</b></div>", unsafe_allow_html=True)
    
    selected = st.session_state.get('selected_member', 'All Members')
    member_df = df[df["member"] == selected].copy() if selected != 'All Members' and not df.empty else df

    if not member_df.empty:
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            date_filter = st.selectbox("DATE FILTER", ["All Time", "Today", "This Week", "Custom Range"], key="td_date")
        
        start_date, end_date = None, None
        if date_filter == "Custom Range":
            with c2:
                default_start = date.today() - timedelta(days=7)
                date_range = st.date_input("SELECT DATES", value=(default_start, date.today()), key="td_custom")
                if isinstance(date_range, tuple):
                    start_date = date_range[0] if len(date_range) > 0 else None
                    end_date = date_range[1] if len(date_range) > 1 else start_date
                else:
                    start_date = end_date = date_range
        
        member_df = apply_date_filter(member_df, date_filter, start_date, end_date)

    display_stat_cards(member_df)

    if member_df.empty:
        st.info("No records found in the selected date range.")
        return

    table_df = member_df.copy()
    table_df["Date"] = table_df["task_date"].apply(lambda x: x.strftime("%b %d, %Y") if pd.notna(x) else "")
    table_df["Project"] = table_df["project"].fillna("")
    
    table_df["Details"] = table_df.apply(lambda r: str(r.get("title") or "") if str(r.get("title") or "").strip() else str(r.get("details") or "")[:80], axis=1)
    table_df["Status"] = table_df["status"].fillna("")
    
    table_df["WC"] = table_df.apply(lambda r: int(r["word_count"]) if r["Project"] == "Summaries" and pd.notna(r["word_count"]) and r["word_count"] > 0 else "", axis=1)
    table_df["Duration"] = table_df.apply(lambda r: str(r["duration"]) if r["Project"] == "Audio" and pd.notna(r["duration"]) and str(r["duration"]).strip() not in ["None", ""] else "", axis=1)
    
    display_cols = ["Date", "Project", "Details", "Status", "WC", "Duration"]
    table_df = table_df[display_cols]

    total_wc = member_df[member_df["project"] == "Summaries"]["word_count"].sum()
    total_dur_mins = sum(member_df[member_df["project"] == "Audio"]["duration"].apply(parse_duration_to_minutes))

    total_row = pd.DataFrame([{
        "Date": "TOTAL", "Project": "", "Details": "", "Status": "",
        "WC": int(total_wc) if total_wc > 0 else "",
        "Duration": format_duration(total_dur_mins) if total_dur_mins > 0 else ""
    }])

    final_df = pd.concat([table_df, total_row], ignore_index=True)
    st.dataframe(final_df, hide_index=True, use_container_width=True)

def reports_page(df: pd.DataFrame):
    st.header("Performance Reports")
    st.write("Filter and view overall team metrics")
    
    display_stat_cards(df)
    
    st.dataframe(df, use_container_width=True)
    
    # Excel Download Export
    if not df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
        excel_data = output.getvalue()
        
        st.download_button(
            label="Download Excel Report",
            data=excel_data,
            file_name=f"Team_Report_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --- 4. MAIN APP ROUTING ---
def main():
    st.set_page_config(page_title="Rawi team | Performance tracker", layout="wide")
    init_db()
    df = load_data()

    # Sidebar Navigation
    with st.sidebar:
        st.title("Rawi team")
        st.caption("Performance tracker")
        st.markdown("### NAVIGATION")
        
        page = st.radio("Go to", ["Team details", "Upload", "Reports"], label_visibility="hidden")
        
        st.markdown("### TEAM MEMBERS")
        members = ["Faten Aish", "Yazan Dmara", "Kamal Arslan", "Nour Aldeen", "Doha Alrefai", "Ali"]
        selected_member = st.radio("Select Member", members, label_visibility="hidden")
        st.session_state.selected_member = selected_member

    # Page Routing
    if page == "Team details":
        team_details_page(df)
    elif page == "Upload":
        upload_page()
    elif page == "Reports":
        reports_page(df)

if __name__ == "__main__":
    main()
