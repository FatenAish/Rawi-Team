import io
import json
import re
import sqlite3
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

APP_TITLE = "Rawi Team Performance"
DB_PATH = Path("rawi_performance.db")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

TEAM_MEMBERS = [
    "Faten Aish",
    "Yazan Dmara",
    "Kamal Arslan",
    "Nour Aldeen",
    "Doha Alrefai",
    "Ali",
]

STATUSES = ["Completed", "In Progress", "Uploaded", "Review"]
PROJECTS = ["Summaries", "Audio", "Meeting", "Social Media & Design", "Other Tasks"]

# Config
st.set_page_config(page_title=APP_TITLE, page_icon="🟣", layout="wide", initial_sidebar_state="expanded")

def inject_css() -> None:
    st.markdown(
        """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        button[kind="primary"] {
            background-color: #7c3aed !important;
            border-color: #7c3aed !important;
            color: #ffffff !important;
        }
        button[kind="primary"]:hover {
            background-color: #6d28d9 !important;
            border-color: #6d28d9 !important;
        }

        div[data-baseweb="calendar"] [aria-selected="true"] {
            background-color: #7c3aed !important;
        }
        
        .page-title {
            font-size: 30px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.02em;
            margin-bottom: 4px;
            text-align: center;
        }
        
        .page-subtitle {
            font-size: 15px;
            color: #64748b;
            margin-bottom: 32px;
            text-align: center;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid #e2e8f0;
        }

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
            padding: 8px 0;
        }

        .sidebar-logo {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            background: #7c3aed;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: 800;
        }

        .sidebar-label {
            color: #94a3b8;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin: 24px 0 12px 0;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }
        
        .metric-box {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }

        .metric-label {
            color: #64748b;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .metric-value {
            color: #0f172a;
            font-size: 28px;
            font-weight: 800;
            margin-top: 8px;
            line-height: 1;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px !important;
            border: 1px solid #e2e8f0 !important;
            background-color: #ffffff !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
            padding: 24px !important;
        }

        .empty-state-box {
            background-color: #f8fafc;
            border: 1px dashed #cbd5e1;
            border-radius: 8px;
            padding: 40px 20px;
            text-align: center;
            color: #64748b;
            margin-top: 16px;
            margin-bottom: 16px;
        }
        
        tr:last-child {
            font-weight: bold !important;
            background-color: #f8fafc !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def parse_duration_to_minutes(d_str):
    if pd.isna(d_str) or not str(d_str).strip():
        return 0.0
    d_str = str(d_str).strip().lower()
    if ':' in d_str:
        parts = d_str.split(':')
        try:
            if len(parts) == 3:
                return int(parts[0]) * 60 + int(parts[1]) + float(parts[2]) / 60
            elif len(parts) == 2:
                return int(parts[0]) + float(parts[1]) / 60
        except ValueError:
            pass
    nums = re.findall(r"[\d\.]+", d_str)
    if not nums:
        return 0.0
    val = float(nums[0])
    if 'h' in d_str: 
        return val * 60
    elif 's' in d_str and 'm' not in d_str and 'h' not in d_str: 
        return val / 60
    else:
        return val

def format_duration(total_minutes):
    if not total_minutes or total_minutes <= 0:
        return ""
    hours = int(total_minutes // 60)
    mins = int(total_minutes % 60)
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{mins}m"

def init_state() -> None:
    if "page" not in st.session_state:
        st.session_state.page = "Upload"
    if "selected_member" not in st.session_state:
        st.session_state.selected_member = TEAM_MEMBERS[0]

def init_db() -> None:
    required_columns = {
        "id": "TEXT PRIMARY KEY",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT",
        "task_date": "TEXT",
        "week_start": "TEXT",
        "member": "TEXT NOT NULL",
        "status": "TEXT NOT NULL",
        "project": "TEXT",
        "title": "TEXT NOT NULL",
        "link": "TEXT",
        "word_count": "INTEGER",
        "duration": "TEXT",
        "details": "TEXT",
        "source_files": "TEXT",
    }

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS performance_records (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                task_date TEXT,
                week_start TEXT,
                member TEXT NOT NULL,
                status TEXT NOT NULL,
                project TEXT,
                title TEXT NOT NULL,
                link TEXT,
                word_count INTEGER,
                duration TEXT,
                details TEXT,
                source_files TEXT
            )
            """
        )
        existing = {row[1] for row in conn.execute("PRAGMA table_info(performance_records)").fetchall()}
        for column, col_type in required_columns.items():
            if column not in existing:
                default_val = "''" if "NOT NULL" in col_type.upper() else "NULL"
                conn.execute(f"ALTER TABLE performance_records ADD COLUMN {column} {col_type} DEFAULT {default_val}")
        conn.commit()

def safe_json_loads(value):
    if not value: return []
    try:
        loaded = json.loads(value)
        return loaded if isinstance(loaded, list) else []
    except Exception: return []

def load_records() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM performance_records ORDER BY task_date DESC, created_at DESC", conn)

    expected_cols = [
        "id", "created_at", "updated_at", "task_date", "week_start", "member", "status", "project", 
        "title", "link", "word_count", "duration", "details", "source_files",
    ]

    if df.empty:
        return pd.DataFrame(columns=expected_cols + ["source_files_list"])

    for col in expected_cols:
        if col not in df.columns: df[col] = None

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")
    df["task_date"] = pd.to_datetime(df["task_date"], errors="coerce").dt.date
    df["week_start"] = pd.to_datetime(df["week_start"], errors="coerce").dt.date
    df["source_files_list"] = df["source_files"].apply(safe_json_loads)
    df["word_count"] = pd.to_numeric(df["word_count"], errors="coerce").fillna(0).astype(int)
    
    # Absolute strict backend data cleaning on load
    df.loc[df["project"] == "Summaries", "duration"] = ""
    df.loc[df["project"] != "Summaries", "word_count"] = 0
    df.loc[df["project"] != "Audio", "duration"] = ""

    return df[expected_cols + ["source_files_list"]]

def save_uploaded_files(record_id: str, uploaded_files) -> list[dict]:
    saved = []
    if not uploaded_files: return saved
    folder = UPLOAD_DIR / record_id
    folder.mkdir(parents=True, exist_ok=True)
    for uploaded_file in uploaded_files:
        safe_name = uploaded_file.name.replace("/", "_").replace("\\", "_")
        output_path = folder / safe_name
        output_path.write_bytes(uploaded_file.getbuffer())
        saved.append({"name": uploaded_file.name, "path": str(output_path), "type": uploaded_file.type or "file", "size": uploaded_file.size})
    return saved

def insert_record(*, task_date: date, member: str, status: str, project: str, title: str = "", link: str = "", word_count: int = 0, duration: str = "", details: str = "", uploaded_files=None) -> str:
    record_id = str(uuid.uuid4())
    files = save_uploaded_files(record_id, uploaded_files)
    now = datetime.now().isoformat(timespec="seconds")
    task_date_obj = task_date if task_date else date.today()
    task_date_str = task_date_obj.isoformat()
    week_start_str = (task_date_obj - timedelta(days=task_date_obj.weekday())).isoformat()
    
    # Enforce clear constraints during data insertion
    if project == "Summaries":
        duration = ""
    else:
        word_count = 0

    word_count_int = int(word_count) if word_count else 0

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO performance_records
            (id, created_at, updated_at, task_date, week_start, member, status, project, title, link,
             word_count, duration, details, source_files)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (record_id, now, now, task_date_str, week_start_str, member, status, project, str(title).strip(), str(link).strip(), word_count_int, str(duration).strip(), str(details).strip(), json.dumps(files, ensure_ascii=False)),
        )
        conn.commit()
    return record_id

def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-logo">R</div>
                <div>
                    <div style="font-weight: 700; font-size: 16px; color: #0f172a;">Rawi team</div>
                    <div style="font-size: 13px; color: #64748b;">Performance tracker</div>
                </div>
            </div>
            """, unsafe_allow_html=True
        )

        st.markdown('<div class="sidebar-label">Navigation</div>', unsafe_allow_html=True)
        nav_items = {"Team Details": "👥 Team details", "Upload": "↑ Upload task", "Reports": "📊 View reports"}
        for page, label in nav_items.items():
            if st.button(label, key=f"nav_{page}", type="primary" if st.session_state.page == page else "secondary", use_container_width=True):
                st.session_state.page = page
                st.rerun()

        st.markdown('<div class="sidebar-label">Team Members</div>', unsafe_allow_html=True)
        for member in TEAM_MEMBERS:
            is_active_member = st.session_state.selected_member == member and st.session_state.page == "Team Details"
            if st.button(f"• {member}", key=f"mem_{member}", type="primary" if is_active_member else "secondary", use_container_width=True):
                st.session_state.selected_member = member
                st.session_state.page = "Team Details"
                st.rerun()

def display_stat_cards(df: pd.DataFrame):
    total_records = len(df)
    completed = int((df["status"] == "Completed").sum()) if not df.empty else 0
    summaries = int((df["project"] == "Summaries").sum()) if not df.empty else 0
    uploaded = int((df["status"] == "Uploaded").sum()) if not df.empty else 0
    reviews = int((df["status"] == "Review").sum()) if not df.empty else 0
    total_wc = int(df["word_count"].sum()) if not df.empty else 0
    total_files = sum(len(x) for x in df["source_files_list"]) if not df.empty else 0

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-box"><div class="metric-label">Records</div><div class="metric-value">{total_records}</div></div>
            <div class="metric-box"><div class="metric-label">Completed</div><div class="metric-value">{completed}</div></div>
            <div class="metric-box"><div class="metric-label">Summaries</div><div class="metric-value">{summaries}</div></div>
            <div class="metric-box"><div class="metric-label">Uploaded</div><div class="metric-value">{uploaded}</div></div>
            <div class="metric-box"><div class="metric-label">Reviews</div><div class="metric-value">{reviews}</div></div>
            <div class="metric-box"><div class="metric-label">Total Words</div><div class="metric-value">{total_wc:,}</div></div>
            <div class="metric-box"><div class="metric-label">Files</div><div class="metric-value">{total_files}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def apply_date_filter(df: pd.DataFrame, date_filter: str, start_date=None, end_date=None) -> pd.DataFrame:
    today = date.today()
    if date_filter == "Today": return df[df["task_date"] == today]
    elif date_filter == "This Week":
        start_of_week = today - timedelta(days=today.weekday())
        return df[df["task_date"] >= start_of_week]
    elif date_filter == "Last Week":
        start_of_this_week = today - timedelta(days=today.weekday())
        return df[(df["task_date"] >= start_of_this_week - timedelta(days=7)) & (df["task_date"] <= start_of_this_week - timedelta(days=1))]
    elif date_filter == "This Month":
        return df[df["task_date"] >= today.replace(day=1)]
    elif date_filter == "Custom Range" and start_date and end_date:
        return df[(df["task_date"] >= start_date) & (df["task_date"] <= end_date)]
    return df

def format_file_names(files):
    if not files:
        return ""
    names = []
    for item in files:
        if isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            if name:
                names.append(name)
        else:
            item_name = str(item).strip()
            if item_name:
                names.append(item_name)
    return ", ".join(names)

def format_link_or_upload(row):
    link = str(row.get("link") or "").strip()
    if link:
        return link
    return format_file_names(row.get("source_files_list") or [])

def format_row_details(row):
    proj = row.get("Project", "")
    title = str(row.get("title") or "").strip()
    details = str(row.get("details") or "").strip()
    
    if proj == "Meeting":
        return f"With: {title}" + (f" | {details}" if details else "")
    elif proj == "Social Media & Design":
        return f"{title} | Qty: {details}"
    elif proj == "Other Tasks":
        return details[:80]
    else:
        return title if title else details[:80]

def get_social_media_totals(source_df: pd.DataFrame) -> dict:
    totals = {"Covers": 0, "Reels": 0}
    if source_df.empty or "project" not in source_df.columns:
        return totals

    social_df = source_df[source_df["project"] == "Social Media & Design"].copy()
    if social_df.empty:
        return totals

    social_df["task_type_clean"] = social_df["title"].fillna("").astype(str).str.strip().str.lower()
    social_df["number_clean"] = pd.to_numeric(social_df["details"], errors="coerce").fillna(0).astype(int)
    totals["Covers"] = int(social_df[social_df["task_type_clean"].isin(["cover", "covers"])]["number_clean"].sum())
    totals["Reels"] = int(social_df[social_df["task_type_clean"].isin(["reel", "reels"])]["number_clean"].sum())
    return totals

def get_summary_status_totals(source_df: pd.DataFrame) -> dict:
    totals = {"Summaries": 0, "Uploaded": 0, "Review": 0}
    if source_df.empty or "project" not in source_df.columns:
        return totals

    summary_df = source_df[source_df["project"] == "Summaries"].copy()
    if summary_df.empty:
        return totals

    totals["Summaries"] = int(len(summary_df))
    totals["Uploaded"] = int((summary_df["status"] == "Uploaded").sum())
    totals["Review"] = int((summary_df["status"] == "Review").sum())
    return totals

def team_details_page(df: pd.DataFrame) -> None:
    st.markdown("<div class='page-title'>Team details</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='page-subtitle'>Performance records for <b>{st.session_state.selected_member}</b></div>", unsafe_allow_html=True)
    
    member_df = df[df["member"] == st.session_state.selected_member].copy() if not df.empty else df

    if not member_df.empty:
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            date_filter = st.selectbox("DATE FILTER", ["All Time", "Today", "This Week", "Last Week", "This Month", "Custom Range"], key="td_date")
        
        start_date, end_date = None, None
        if date_filter == "Custom Range":
            with c2:
                date_range = st.date_input("SELECT DATES", value=(date.today() - timedelta(days=7), date.today()), key="td_custom")
                if isinstance(date_range, tuple):
                    start_date = date_range[0] if len(date_range) > 0 else None
                    end_date = date_range[1] if len(date_range) > 1 else start_date
                else:
                    start_date = end_date = date_range
        
        member_df = apply_date_filter(member_df, date_filter, start_date, end_date)

    display_stat_cards(member_df)

    if member_df.empty:
        st.info(f"No records found for {st.session_state.selected_member} in the selected date range.")
        return

    table_df = member_df.copy()
    table_df["Date"] = table_df["task_date"].apply(lambda x: x.strftime("%b %d, %Y") if pd.notna(x) else "")
    table_df["Project"] = table_df["project"].fillna("")
    table_df["Name"] = table_df.apply(lambda r: str(r["title"]).strip() if r["Project"] == "Summaries" and pd.notna(r["title"]) else "", axis=1)
    table_df["URL"] = table_df.apply(lambda r: str(r["link"]).strip() if r["Project"] == "Summaries" and pd.notna(r["link"]) else "", axis=1)
    table_df["Task Type"] = table_df.apply(lambda r: str(r["title"]).strip() if r["Project"] == "Social Media & Design" and pd.notna(r["title"]) else "", axis=1)
    table_df["Number"] = table_df.apply(lambda r: str(r["details"]).strip() if r["Project"] == "Social Media & Design" and pd.notna(r["details"]) else "", axis=1)
    table_df["Details"] = table_df.apply(lambda r: str(r["details"]).strip() if r["Project"] == "Other Tasks" and pd.notna(r["details"]) else "", axis=1)
    table_df["Link"] = table_df.apply(format_link_or_upload, axis=1)
    table_df["Status"] = table_df["status"].fillna("")
    
    # Format and enforce completely blank column outputs for cross-metrics
    table_df["WC"] = table_df.apply(lambda r: int(r["word_count"]) if r["Project"] == "Summaries" and r["word_count"] > 0 else "", axis=1)
    table_df["Duration"] = table_df.apply(lambda r: str(r["duration"]) if r["Project"] == "Audio" and pd.notna(r["duration"]) and str(r["duration"]).strip() else "", axis=1)
    
    display_cols = ["Date", "Project"]
    show_summary_cols = (member_df["project"] == "Summaries").any()
    show_social_cols = (member_df["project"] == "Social Media & Design").any()
    show_other_details_col = (member_df["project"] == "Other Tasks").any()
    show_duration_col = (member_df["project"] == "Audio").any()
    if show_summary_cols:
        display_cols.extend(["Name", "URL", "WC"])
    if show_social_cols:
        display_cols.extend(["Task Type", "Number"])
    if show_other_details_col:
        display_cols.append("Details")
    if show_social_cols or show_other_details_col or show_duration_col:
        display_cols.append("Link")
    if not show_summary_cols or show_social_cols or show_other_details_col or show_duration_col:
        display_cols.append("Status")
    if show_duration_col:
        display_cols.append("Duration")
    table_df = table_df[display_cols]

    total_wc = member_df[member_df["project"] == "Summaries"]["word_count"].sum()
    total_dur_mins = sum(member_df[member_df["project"] == "Audio"]["duration"].apply(parse_duration_to_minutes))

    total_rows = []
    if show_summary_cols:
        summary_totals = get_summary_status_totals(member_df)
        summary_total_rows = [
            ("TOTAL SUMMARIES", summary_totals["Summaries"]),
            ("TOTAL UPLOADED", summary_totals["Uploaded"]),
            ("TOTAL REVIEW", summary_totals["Review"]),
        ]
        for label, count_value in summary_total_rows:
            row_data = {"Date": label, "Project": "Summaries", "Name": count_value, "URL": "", "WC": int(total_wc) if label == "TOTAL SUMMARIES" and total_wc > 0 else ""}
            if show_social_cols:
                row_data["Task Type"] = ""
                row_data["Number"] = ""
            if show_other_details_col:
                row_data["Details"] = ""
            if show_social_cols or show_other_details_col or show_duration_col:
                row_data["Link"] = ""
            if not show_summary_cols or show_social_cols or show_other_details_col or show_duration_col:
                row_data["Status"] = ""
            if show_duration_col:
                row_data["Duration"] = ""
            total_rows.append(row_data)

    if show_social_cols:
        social_totals = get_social_media_totals(member_df)
        for task_type in ["Covers", "Reels"]:
            row_data = {"Date": f"TOTAL {task_type.upper()}", "Project": "Social Media & Design", "Task Type": task_type, "Number": social_totals[task_type]}
            if show_summary_cols:
                row_data["Name"] = ""
                row_data["URL"] = ""
                row_data["WC"] = ""
            if show_other_details_col:
                row_data["Details"] = ""
            if show_social_cols or show_other_details_col or show_duration_col:
                row_data["Link"] = ""
            if not show_summary_cols or show_social_cols or show_other_details_col or show_duration_col:
                row_data["Status"] = ""
            if show_duration_col:
                row_data["Duration"] = ""
            total_rows.append(row_data)

    if show_duration_col:
        total_row_data = {"Date": "TOTAL DURATION", "Project": ""}
        if show_summary_cols:
            total_row_data["Name"] = ""
            total_row_data["URL"] = ""
            total_row_data["WC"] = ""
        if show_social_cols:
            total_row_data["Task Type"] = ""
            total_row_data["Number"] = ""
        if show_other_details_col:
            total_row_data["Details"] = ""
        if show_social_cols or show_other_details_col or show_duration_col:
            total_row_data["Link"] = ""
        if not show_summary_cols or show_social_cols or show_other_details_col or show_duration_col:
            total_row_data["Status"] = ""
        total_row_data["Duration"] = format_duration(total_dur_mins) if total_dur_mins > 0 else ""
        total_rows.append(total_row_data)

    final_df = pd.concat([table_df, pd.DataFrame(total_rows)], ignore_index=True) if total_rows else table_df

    st.dataframe(final_df, hide_index=True, use_container_width=True)

def upload_page() -> None:
    spacer_left, main_col, spacer_right = st.columns([1, 2, 1])
    with main_col:
        st.markdown("<div class='page-title'>Upload task</div>", unsafe_allow_html=True)
        st.markdown("<div class='page-subtitle'>Record a new task for a team member</div>", unsafe_allow_html=True)

        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                default_idx = TEAM_MEMBERS.index(st.session_state.selected_member) + 1 if st.session_state.selected_member in TEAM_MEMBERS else 0
                member = st.selectbox("TEAM MEMBER", ["Select member..."] + TEAM_MEMBERS, index=default_idx)
            with c2:
                task_date = st.date_input("DATE", value=date.today())

            c3, c4 = st.columns(2)
            with c3:
                status = st.selectbox("STATUS", ["Select status..."] + STATUSES)
            with c4:
                project = st.selectbox("PROJECT", ["Select project..."] + PROJECTS)

            title, link, duration, details = "", "", "", ""
            word_count = 0
            uploaded_files = None

            if project == "Select project...":
                st.markdown('<div class="empty-state-box"><div style="font-size: 15px; font-weight: 500; color: #475569;">Select a project type above</div><div style="font-size: 13px; margin-top: 4px;">Task fields will appear here</div></div>', unsafe_allow_html=True)
            else:
                st.divider()
                if project == "Summaries":
                    s1, s2 = st.columns([3, 1])
                    with s1:
                        title = st.text_input("NAME")
                    with s2:
                        word_count = st.number_input("WC", min_value=0, step=1, value=0)
                    link = st.text_input("URL", placeholder="https://docs.google.com/...")
                    duration = "" # Force empty string variable space allocation

                elif project == "Audio":
                    a1, a2 = st.columns([3, 1])
                    with a1: title = st.text_input("AUDIO NAME")
                    with a2: duration = st.text_input("DURATION", placeholder="00:15:00")
                    link = st.text_input("LINK", placeholder="https://...")
                    word_count = 0

                elif project == "Meeting":
                    title = st.text_input("WITH WHO", placeholder="e.g., Client Name, Manager, etc.")
                    details = st.text_area("MEETING DETAILS", height=120)
                    
                elif project == "Social Media & Design":
                    sm1, sm2 = st.columns([3, 1])
                    with sm1:
                        sm_type = st.selectbox("TASK TYPE", ["Covers", "Reels", "Other Tasks"])
                    with sm2:
                        sm_qty = st.number_input("HOW MANY", min_value=1, step=1, value=1)
                    title = sm_type
                    details = str(sm_qty)
                    link = st.text_input("LINK", placeholder="https://...")

                elif project == "Other Tasks":
                    details = st.text_area("TASK DETAILS", height=120)
                    attachment_type = st.radio("LINK OR IMAGE UPLOAD", ["Link", "Image/File Upload"], horizontal=True)
                    if attachment_type == "Link":
                        link = st.text_input("LINK", placeholder="https://...")
                        uploaded_files = None
                    else:
                        link = ""
                        uploaded_files = st.file_uploader("UPLOAD IMAGE/FILE", accept_multiple_files=True)

            st.markdown("<br>", unsafe_allow_html=True)
            save_clicked = st.button("Save Task", use_container_width=True, type="primary")

        if save_clicked:
            errors = []
            if member == "Select member...": errors.append("Select a team member.")
            if status == "Select status...": errors.append("Select a status.")
            if project == "Select project...": errors.append("Select a project type.")

            if project == "Summaries":
                if not title.strip(): errors.append("Provide a name.")
                if not link.strip(): errors.append("Provide a URL.")
            elif project == "Audio":
                if not title.strip(): errors.append("Provide an audio name.")
                if not duration.strip(): errors.append("Provide a duration.")
                if not link.strip(): errors.append("Provide a URL.")
            elif project == "Meeting":
                if not title.strip(): errors.append("Provide who the meeting was with.")
                if not details.strip(): errors.append("Provide meeting details.")
            elif project == "Other Tasks":
                if not details.strip(): errors.append("Provide task details.")
                if not link.strip() and not uploaded_files: errors.append("Provide a link or upload an image/file.")

            if errors:
                for err in errors: st.error(err)
            else:
                try:
                    insert_record(task_date=task_date, member=member, status=status, project=project, title=title, link=link, word_count=word_count, duration=duration, details=details, uploaded_files=uploaded_files)
                    st.success(f"Task saved for {member}!")
                    st.session_state.selected_member = member
                except sqlite3.IntegrityError as e: st.error(f"Database Error: {e}.")
                except Exception as e: st.error(f"An unexpected error occurred: {e}")

def generate_excel_report(report_df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if report_df.empty:
            pd.DataFrame(["No data available"]).to_excel(writer, sheet_name="Empty", header=False, index=False)
            return output.getvalue()
            
        for member in report_df['member'].unique():
            m_df = report_df[report_df['member'] == member].copy()
            tot_wc = m_df[m_df['project'] == 'Summaries']['word_count'].sum()
            tot_dur_mins = sum(m_df[m_df['project'] == 'Audio']['duration'].apply(parse_duration_to_minutes))
            
            export_df = m_df[["task_date", "project", "title", "details", "link", "status", "word_count", "duration"]].copy()
            export_df.rename(columns={"task_date": "Date", "project": "Project", "title": "Raw Name", "details": "Details", "link": "Raw Link", "status": "Status", "word_count": "WC", "duration": "Duration"}, inplace=True)
            export_df["Name"] = export_df.apply(lambda r: str(r["Raw Name"]).strip() if r["Project"] == "Summaries" and pd.notna(r["Raw Name"]) else "", axis=1)
            export_df["URL"] = export_df.apply(lambda r: str(r["Raw Link"]).strip() if r["Project"] == "Summaries" and pd.notna(r["Raw Link"]) else "", axis=1)
            export_df["Link"] = m_df.apply(format_link_or_upload, axis=1).values
            export_df["Task Type"] = export_df.apply(lambda r: str(r["Raw Name"]).strip() if r["Project"] == "Social Media & Design" and pd.notna(r["Raw Name"]) else "", axis=1)
            export_df["Number"] = export_df.apply(lambda r: str(r["Details"]).strip() if r["Project"] == "Social Media & Design" and pd.notna(r["Details"]) else "", axis=1)
            export_df["Details"] = export_df.apply(lambda r: str(r["Details"]).strip() if r["Project"] == "Other Tasks" and pd.notna(r["Details"]) else "", axis=1)
            export_df["WC"] = export_df.apply(lambda r: int(r["WC"]) if r["Project"] == "Summaries" and r["WC"] > 0 else "", axis=1)
            export_df["Duration"] = export_df.apply(lambda r: str(r["Duration"]) if r["Project"] == "Audio" and r["Duration"] else "", axis=1)

            export_cols = ["Date", "Project"]
            show_summary_cols = (m_df["project"] == "Summaries").any()
            show_social_cols = (m_df["project"] == "Social Media & Design").any()
            show_other_details_col = (m_df["project"] == "Other Tasks").any()
            show_duration_col = (m_df["project"] == "Audio").any()
            if show_summary_cols:
                export_cols.extend(["Name", "URL", "WC"])
            if show_social_cols:
                export_cols.extend(["Task Type", "Number"])
            if show_other_details_col:
                export_cols.append("Details")
            if show_social_cols or show_other_details_col or show_duration_col:
                export_cols.append("Link")
            if not show_summary_cols or show_social_cols or show_other_details_col or show_duration_col:
                export_cols.append("Status")
            if show_duration_col:
                export_cols.append("Duration")
            export_df = export_df[export_cols]

            total_rows = []
            if show_summary_cols:
                summary_totals = get_summary_status_totals(m_df)
                summary_total_rows = [
                    ("TOTAL SUMMARIES", summary_totals["Summaries"]),
                    ("TOTAL UPLOADED", summary_totals["Uploaded"]),
                    ("TOTAL REVIEW", summary_totals["Review"]),
                ]
                for label, count_value in summary_total_rows:
                    row_data = {"Date": label, "Project": "Summaries", "Name": count_value, "URL": "", "WC": int(tot_wc) if label == "TOTAL SUMMARIES" and tot_wc > 0 else ""}
                    if show_social_cols:
                        row_data["Task Type"] = ""
                        row_data["Number"] = ""
                    if show_other_details_col:
                        row_data["Details"] = ""
                    if show_social_cols or show_other_details_col or show_duration_col:
                        row_data["Link"] = ""
                    if not show_summary_cols or show_social_cols or show_other_details_col or show_duration_col:
                        row_data["Status"] = ""
                    if show_duration_col:
                        row_data["Duration"] = ""
                    total_rows.append(row_data)

            if show_social_cols:
                social_totals = get_social_media_totals(m_df)
                for task_type in ["Covers", "Reels"]:
                    row_data = {"Date": f"TOTAL {task_type.upper()}", "Project": "Social Media & Design", "Task Type": task_type, "Number": social_totals[task_type]}
                    if show_summary_cols:
                        row_data["Name"] = ""
                        row_data["URL"] = ""
                        row_data["WC"] = ""
                    if show_other_details_col:
                        row_data["Details"] = ""
                    if show_social_cols or show_other_details_col or show_duration_col:
                        row_data["Link"] = ""
                    if not show_summary_cols or show_social_cols or show_other_details_col or show_duration_col:
                        row_data["Status"] = ""
                    if show_duration_col:
                        row_data["Duration"] = ""
                    total_rows.append(row_data)

            if show_duration_col:
                total_row_data = {"Date": "TOTAL DURATION", "Project": ""}
                if show_summary_cols:
                    total_row_data["Name"] = ""
                    total_row_data["URL"] = ""
                    total_row_data["WC"] = ""
                if show_social_cols:
                    total_row_data["Task Type"] = ""
                    total_row_data["Number"] = ""
                if show_other_details_col:
                    total_row_data["Details"] = ""
                if show_social_cols or show_other_details_col or show_duration_col:
                    total_row_data["Link"] = ""
                if not show_summary_cols or show_social_cols or show_other_details_col or show_duration_col:
                    total_row_data["Status"] = ""
                total_row_data["Duration"] = format_duration(tot_dur_mins) if tot_dur_mins > 0 else ""
                total_rows.append(total_row_data)

            if total_rows:
                export_df = pd.concat([export_df, pd.DataFrame(total_rows)], ignore_index=True)
            
            safe_sheet_name = re.sub(r'[\[\]\:\*\?/\\]', '', str(member))[:31]
            export_df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            
    return output.getvalue()

def reports_page(df: pd.DataFrame) -> None:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<div class='page-title' style='text-align: left;'>Performance Reports</div>", unsafe_allow_html=True)
        st.markdown("<div class='page-subtitle' style='text-align: left;'>Filter and view overall team metrics</div>", unsafe_allow_html=True)

    if df.empty:
        st.info("No records available to report.")
        return

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        date_filter = st.selectbox("DATE FILTER", ["All Time", "Today", "This Week", "Last Week", "This Month", "Custom Range"])
        start_date, end_date = None, None
        if date_filter == "Custom Range":
            date_range = st.date_input("SELECT DATES", value=(date.today() - timedelta(days=7), date.today()))
            if isinstance(date_range, tuple):
                start_date = date_range[0] if len(date_range) > 0 else None
                end_date = date_range[1] if len(date_range) > 1 else start_date
            else:
                start_date = end_date = date_range

    with f2: member_filter = st.selectbox("MEMBER", ["All Members"] + TEAM_MEMBERS)
    with f3: project_filter = st.selectbox("PROJECT", ["All Projects"] + PROJECTS)
    with f4: status_filter = st.selectbox("STATUS", ["All Statuses"] + STATUSES)

    report_df = apply_date_filter(df, date_filter, start_date, end_date)
    if member_filter != "All Members": report_df = report_df[report_df["member"] == member_filter]
    if project_filter != "All Projects": report_df = report_df[report_df["project"] == project_filter]
    if status_filter != "All Statuses": report_df = report_df[report_df["status"] == status_filter]

    display_stat_cards(report_df)

    with col2:
        st.write("") 
        if not report_df.empty:
            try:
                import openpyxl
                excel_file = generate_excel_report(report_df)
                st.download_button(label="📥 Download Excel Report", data=excel_file, file_name=f"Team_Report_{date.today().strftime('%Y-%m-%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", use_container_width=True)
            except ImportError:
                st.error("⚠️ Add 'openpyxl' to requirements.txt to enable Excel downloads.")

    st.markdown("### Detailed Records")
    if report_df.empty:
        st.warning("No records match your filters.")
    else:
        table_df = report_df.copy()
        table_df["Date"] = table_df["task_date"].apply(lambda x: x.strftime("%b %d, %Y") if pd.notna(x) else "")
        table_df["Member"] = table_df["member"]
        table_df["Project"] = table_df["project"].fillna("")
        table_df["Name"] = table_df.apply(lambda r: str(r["title"]).strip() if r["Project"] == "Summaries" and pd.notna(r["title"]) else "", axis=1)
        table_df["URL"] = table_df.apply(lambda r: str(r["link"]).strip() if r["Project"] == "Summaries" and pd.notna(r["link"]) else "", axis=1)
        table_df["Task Type"] = table_df.apply(lambda r: str(r["title"]).strip() if r["Project"] == "Social Media & Design" and pd.notna(r["title"]) else "", axis=1)
        table_df["Number"] = table_df.apply(lambda r: str(r["details"]).strip() if r["Project"] == "Social Media & Design" and pd.notna(r["details"]) else "", axis=1)
        table_df["Details"] = table_df.apply(lambda r: str(r["details"]).strip() if r["Project"] == "Other Tasks" and pd.notna(r["details"]) else "", axis=1)
        table_df["Link"] = table_df.apply(format_link_or_upload, axis=1)
        table_df["Status"] = table_df["status"].fillna("")
        
        # Absolute strict view rendering filters to completely remove duration traces
        table_df["WC"] = table_df.apply(lambda r: int(r["word_count"]) if r["Project"] == "Summaries" and r["word_count"] > 0 else "", axis=1)
        table_df["Duration"] = table_df.apply(lambda r: str(r["duration"]) if r["Project"] == "Audio" and pd.notna(r["duration"]) and str(r["duration"]).strip() else "", axis=1)
        
        display_cols = ["Date", "Member", "Project"]
        show_summary_cols = (report_df["project"] == "Summaries").any()
        show_social_cols = (report_df["project"] == "Social Media & Design").any()
        show_other_details_col = (report_df["project"] == "Other Tasks").any()
        show_duration_col = (report_df["project"] == "Audio").any()
        if show_summary_cols:
            display_cols.extend(["Name", "URL", "WC"])
        if show_social_cols:
            display_cols.extend(["Task Type", "Number"])
        if show_other_details_col:
            display_cols.append("Details")
        if show_social_cols or show_other_details_col or show_duration_col:
            display_cols.append("Link")
        if not show_summary_cols or show_social_cols or show_other_details_col or show_duration_col:
            display_cols.append("Status")
        if show_duration_col:
            display_cols.append("Duration")
        table_df = table_df[display_cols]

        total_wc = report_df[report_df["project"] == "Summaries"]["word_count"].sum()
        total_dur_mins = sum(report_df[report_df["project"] == "Audio"]["duration"].apply(parse_duration_to_minutes))

        total_rows = []
        if show_summary_cols:
            summary_totals = get_summary_status_totals(report_df)
            summary_total_rows = [
                ("TOTAL SUMMARIES", summary_totals["Summaries"]),
                ("TOTAL UPLOADED", summary_totals["Uploaded"]),
                ("TOTAL REVIEW", summary_totals["Review"]),
            ]
            for label, count_value in summary_total_rows:
                row_data = {"Date": label, "Member": "", "Project": "Summaries", "Name": count_value, "URL": "", "WC": int(total_wc) if label == "TOTAL SUMMARIES" and total_wc > 0 else ""}
                if show_social_cols:
                    row_data["Task Type"] = ""
                    row_data["Number"] = ""
                if show_other_details_col:
                    row_data["Details"] = ""
                if show_social_cols or show_other_details_col or show_duration_col:
                    row_data["Link"] = ""
                if not show_summary_cols or show_social_cols or show_other_details_col or show_duration_col:
                    row_data["Status"] = ""
                if show_duration_col:
                    row_data["Duration"] = ""
                total_rows.append(row_data)

        if show_social_cols:
            social_totals = get_social_media_totals(report_df)
            for task_type in ["Covers", "Reels"]:
                row_data = {"Date": f"TOTAL {task_type.upper()}", "Member": "", "Project": "Social Media & Design", "Task Type": task_type, "Number": social_totals[task_type]}
                if show_summary_cols:
                    row_data["Name"] = ""
                    row_data["URL"] = ""
                    row_data["WC"] = ""
                if show_other_details_col:
                    row_data["Details"] = ""
                if show_social_cols or show_other_details_col or show_duration_col:
                    row_data["Link"] = ""
                if not show_summary_cols or show_social_cols or show_other_details_col or show_duration_col:
                    row_data["Status"] = ""
                if show_duration_col:
                    row_data["Duration"] = ""
                total_rows.append(row_data)

        if show_duration_col:
            total_row_data = {"Date": "TOTAL DURATION", "Member": "", "Project": ""}
            if show_summary_cols:
                total_row_data["Name"] = ""
                total_row_data["URL"] = ""
                total_row_data["WC"] = ""
            if show_social_cols:
                total_row_data["Task Type"] = ""
                total_row_data["Number"] = ""
            if show_other_details_col:
                total_row_data["Details"] = ""
            if show_social_cols or show_other_details_col or show_duration_col:
                total_row_data["Link"] = ""
            if not show_summary_cols or show_social_cols or show_other_details_col or show_duration_col:
                total_row_data["Status"] = ""
            total_row_data["Duration"] = format_duration(total_dur_mins) if total_dur_mins > 0 else ""
            total_rows.append(total_row_data)

        final_df = pd.concat([table_df, pd.DataFrame(total_rows)], ignore_index=True) if total_rows else table_df

        st.dataframe(final_df, hide_index=True, use_container_width=True)

def main() -> None:
    inject_css()
    init_state()
    init_db()
    df = load_records()
    render_sidebar()
    if st.session_state.page == "Team Details": team_details_page(df)
    elif st.session_state.page == "Upload": upload_page()
    elif st.session_state.page == "Reports": reports_page(df)

if __name__ == "__main__":
    main()
