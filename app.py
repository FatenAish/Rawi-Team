import html
import json
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
PROJECTS = ["Summaries", "Audio", "Other Tasks"]

STATUS_MIGRATION = {
    "In Process": "In Progress",
    "Upload": "Uploaded",
}

PROJECT_MIGRATION = {
    "Other tasks": "Other Tasks",
}

DATE_FILTERS = ["All Time", "Today", "This Week", "Last Week", "This Month"]

st.set_page_config(page_title=APP_TITLE, page_icon="R", layout="wide")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --purple: #7c3aed;
            --purple-dark: #5b21b6;
            --purple-soft: #f5f3ff;
            --purple-border: #ddd6fe;
            --bg: #f8fafc;
            --panel: #ffffff;
            --border: #e5e7eb;
            --border-soft: #f1f5f9;
            --text: #111827;
            --muted: #6b7280;
        }

        .stApp {
            background: var(--bg);
        }

        .block-container {
            padding-top: 1.35rem;
            padding-bottom: 2.5rem;
            max-width: 1480px;
        }

        h1, h2, h3, p, div, span, label, input, textarea, button {
            font-family: Inter, Arial, sans-serif;
        }

        h1, h2, h3 {
            color: var(--text);
            letter-spacing: -0.03em;
        }

        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.2rem;
        }

        .brand-row {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 4px 4px 20px 4px;
            border-bottom: 1px solid var(--border-soft);
            margin-bottom: 16px;
        }

        .brand-mark {
            width: 44px;
            height: 44px;
            border-radius: 14px;
            background: linear-gradient(135deg, var(--purple), #a855f7);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            font-size: 22px;
            box-shadow: 0 10px 24px rgba(124, 58, 237, 0.22);
        }

        .brand-title {
            color: var(--text);
            font-size: 19px;
            font-weight: 900;
            line-height: 1.05;
        }

        .brand-subtitle {
            color: var(--muted);
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-top: 3px;
        }

        .side-label {
            color: #8b5cf6;
            font-size: 11px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.11em;
            padding: 12px 4px 8px 4px;
        }

        .sidebar-active,
        .member-active {
            background: var(--purple-soft);
            color: var(--purple-dark);
            border: 1px solid var(--purple-border);
            border-left: 5px solid var(--purple);
            border-radius: 13px;
            padding: 10px 12px;
            font-weight: 900;
            margin: 4px 0 7px 0;
            box-shadow: 0 1px 2px rgba(17, 24, 39, 0.03);
        }

        section[data-testid="stSidebar"] .stButton > button {
            width: 100%;
            justify-content: flex-start;
            text-align: left;
            color: #4b5563;
            background: transparent;
            border: 1px solid transparent;
            border-radius: 12px;
            font-weight: 800;
            padding: 0.58rem 0.7rem;
        }

        section[data-testid="stSidebar"] .stButton > button:hover {
            background: var(--purple-soft);
            color: var(--purple-dark);
            border-color: var(--purple-border);
        }

        .page-kicker {
            color: var(--purple);
            font-size: 12px;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.13em;
            margin-bottom: 6px;
        }

        .page-title {
            color: var(--text);
            font-size: 30px;
            font-weight: 950;
            letter-spacing: -0.04em;
            margin: 0;
        }

        .page-subtitle {
            color: var(--muted);
            font-size: 14px;
            margin: 5px 0 18px 0;
        }

        .panel {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
            margin-bottom: 18px;
        }

        .form-panel {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 22px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
            margin-top: 4px;
        }

        .section-title {
            color: var(--text);
            font-size: 16px;
            font-weight: 950;
            margin: 0 0 4px 0;
        }

        .section-subtitle {
            color: var(--muted);
            font-size: 13px;
            margin-bottom: 16px;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(130px, 1fr));
            gap: 14px;
            margin: 14px 0 18px 0;
        }

        .metric-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 17px;
            padding: 17px 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.035);
            position: relative;
            overflow: hidden;
        }

        .metric-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 5px;
            background: var(--purple);
        }

        .metric-label {
            color: var(--muted);
            font-size: 11px;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .metric-value {
            color: var(--text);
            font-size: 29px;
            line-height: 1.1;
            font-weight: 950;
            letter-spacing: -0.05em;
            margin-top: 7px;
        }

        .rawi-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            overflow: hidden;
            border: 1px solid var(--border);
            border-radius: 18px;
            background: #ffffff;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        }

        .rawi-table thead th {
            background: var(--purple-soft);
            color: var(--purple-dark);
            font-size: 11px;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            padding: 13px 14px;
            border-bottom: 1px solid var(--purple-border);
            text-align: left;
        }

        .rawi-table tbody td {
            color: #374151;
            font-size: 13px;
            padding: 13px 14px;
            border-bottom: 1px solid var(--border-soft);
            vertical-align: top;
        }

        .rawi-table tbody tr:last-child td {
            border-bottom: none;
        }

        .rawi-table tbody tr:hover td {
            background: #faf5ff;
        }

        .tag {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 4px 9px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 950;
            white-space: nowrap;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .tag-purple {
            color: var(--purple-dark);
            background: var(--purple-soft);
            border: 1px solid var(--purple-border);
        }

        .tag-filled {
            color: white;
            background: var(--purple);
            border: 1px solid var(--purple);
        }

        .detail-main {
            font-weight: 850;
            color: var(--text);
            margin-bottom: 3px;
        }

        .detail-sub {
            color: var(--muted);
            font-size: 12px;
            overflow-wrap: anywhere;
        }

        .empty-box {
            background: #ffffff;
            border: 1px dashed var(--purple-border);
            border-radius: 18px;
            color: var(--muted);
            padding: 28px;
            text-align: center;
            font-weight: 750;
        }

        .stButton > button[kind="primary"],
        button[data-testid="baseButton-primary"] {
            background: var(--purple) !important;
            color: #ffffff !important;
            border-color: var(--purple) !important;
            border-radius: 12px !important;
            font-weight: 950 !important;
            justify-content: center !important;
        }

        .stButton > button[kind="primary"]:hover,
        button[data-testid="baseButton-primary"]:hover {
            background: var(--purple-dark) !important;
            border-color: var(--purple-dark) !important;
        }

        .stDownloadButton > button {
            border-radius: 12px !important;
            font-weight: 850 !important;
            border: 1px solid var(--purple-border) !important;
            color: var(--purple-dark) !important;
        }

        div[data-testid="stSelectbox"] label,
        div[data-testid="stDateInput"] label,
        div[data-testid="stTextInput"] label,
        div[data-testid="stTextArea"] label,
        div[data-testid="stNumberInput"] label,
        div[data-testid="stFileUploader"] label {
            color: #4b5563 !important;
            font-size: 12px !important;
            font-weight: 950 !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        @media (max-width: 1050px) {
            .metric-grid {
                grid-template-columns: repeat(2, minmax(130px, 1fr));
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    if "page" not in st.session_state:
        st.session_state.page = "Team Details"
    if "selected_member" not in st.session_state:
        st.session_state.selected_member = TEAM_MEMBERS[0]


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS performance_records (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                task_date TEXT,
                member TEXT NOT NULL,
                status TEXT NOT NULL,
                project TEXT,
                summary_name TEXT,
                link TEXT,
                word_count INTEGER,
                duration TEXT,
                details TEXT,
                source_files TEXT
            )
            """
        )

        existing_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(performance_records)").fetchall()
        }

        columns_to_add = {
            "updated_at": "TEXT",
            "task_date": "TEXT",
            "status": "TEXT",
            "project": "TEXT",
            "summary_name": "TEXT",
            "link": "TEXT",
            "word_count": "INTEGER",
            "duration": "TEXT",
            "details": "TEXT",
            "source_files": "TEXT",
        }

        for column, column_type in columns_to_add.items():
            if column not in existing_columns:
                conn.execute(f"ALTER TABLE performance_records ADD COLUMN {column} {column_type}")

        conn.commit()


def safe_json_loads(value) -> list:
    if not value:
        return []
    try:
        data = json.loads(value)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def load_records() -> pd.DataFrame:
    expected_cols = [
        "id",
        "created_at",
        "updated_at",
        "task_date",
        "member",
        "status",
        "project",
        "summary_name",
        "link",
        "word_count",
        "duration",
        "details",
        "source_files",
    ]

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            "SELECT * FROM performance_records ORDER BY task_date DESC, created_at DESC",
            conn,
        )

    if df.empty:
        return pd.DataFrame(columns=expected_cols + ["source_files_list"])

    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    if "title" in df.columns:
        df["summary_name"] = df["summary_name"].fillna(df["title"])
    if "week_start" in df.columns:
        df["task_date"] = df["task_date"].fillna(df["week_start"])
    if "source_links" in df.columns:
        df["link"] = df["link"].fillna(
            df["source_links"].apply(lambda value: safe_json_loads(value)[0] if safe_json_loads(value) else "")
        )

    df["status"] = df["status"].replace(STATUS_MIGRATION).fillna("")
    df["project"] = df["project"].replace(PROJECT_MIGRATION).fillna("")
    df["summary_name"] = df["summary_name"].fillna("")
    df["link"] = df["link"].fillna("")
    df["duration"] = df["duration"].fillna("")
    df["details"] = df["details"].fillna("")
    df["member"] = df["member"].fillna("")

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")
    df["task_date"] = pd.to_datetime(df["task_date"], errors="coerce").dt.date
    df["word_count"] = pd.to_numeric(df["word_count"], errors="coerce").fillna(0).astype(int)
    df["source_files_list"] = df["source_files"].apply(safe_json_loads)

    return df[expected_cols + ["source_files_list"]]


def save_uploaded_files(record_id: str, uploaded_files) -> list[dict]:
    saved_files = []
    if not uploaded_files:
        return saved_files

    record_folder = UPLOAD_DIR / record_id
    record_folder.mkdir(parents=True, exist_ok=True)

    for uploaded_file in uploaded_files:
        safe_name = uploaded_file.name.replace("/", "_").replace("\\", "_")
        output_path = record_folder / safe_name
        output_path.write_bytes(uploaded_file.getbuffer())
        saved_files.append(
            {
                "name": uploaded_file.name,
                "path": str(output_path),
                "type": uploaded_file.type or "file",
                "size": uploaded_file.size,
            }
        )

    return saved_files


def insert_record(
    *,
    task_date: date,
    member: str,
    status: str,
    project: str,
    summary_name: str = "",
    link: str = "",
    word_count: int = 0,
    duration: str = "",
    details: str = "",
    uploaded_files=None,
) -> str:
    record_id = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")
    saved_files = save_uploaded_files(record_id, uploaded_files)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO performance_records
            (id, created_at, updated_at, task_date, member, status, project,
             summary_name, link, word_count, duration, details, source_files)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                now,
                now,
                task_date.isoformat(),
                member,
                status,
                project,
                summary_name.strip(),
                link.strip(),
                int(word_count or 0),
                duration.strip(),
                details.strip(),
                json.dumps(saved_files, ensure_ascii=False),
            ),
        )
        conn.commit()

    return record_id


def delete_record(record_id: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM performance_records WHERE id = ?", (record_id,))
        conn.commit()


def update_record(
    *,
    record_id: str,
    status: str,
    summary_name: str,
    link: str,
    word_count: int,
    duration: str,
    details: str,
) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE performance_records
            SET updated_at = ?, status = ?, summary_name = ?, link = ?, word_count = ?,
                duration = ?, details = ?
            WHERE id = ?
            """,
            (
                now,
                status,
                summary_name.strip(),
                link.strip(),
                int(word_count or 0),
                duration.strip(),
                details.strip(),
                record_id,
            ),
        )
        conn.commit()


def apply_date_filter(df: pd.DataFrame, filter_name: str) -> pd.DataFrame:
    if df.empty or filter_name == "All Time":
        return df

    today = date.today()
    if filter_name == "Today":
        start, end = today, today
    elif filter_name == "This Week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
    elif filter_name == "Last Week":
        this_week = today - timedelta(days=today.weekday())
        start = this_week - timedelta(days=7)
        end = start + timedelta(days=6)
    elif filter_name == "This Month":
        start, end = today.replace(day=1), today
    else:
        return df

    return df[(df["task_date"] >= start) & (df["task_date"] <= end)].copy()


def escape(value) -> str:
    return html.escape(str(value or ""))


def file_count(files: list) -> int:
    return len(files) if isinstance(files, list) else 0


def build_details(row: pd.Series) -> tuple[str, str]:
    project = row.get("project", "")
    files = file_count(row.get("source_files_list", []))

    if project == "Summaries":
        main = row.get("summary_name") or "Untitled summary"
        sub_parts = []
        if row.get("link"):
            sub_parts.append(row.get("link"))
        if row.get("word_count"):
            sub_parts.append(f"{int(row.get('word_count')):,} words")
        return main, " · ".join(sub_parts)

    if project == "Audio":
        main = row.get("summary_name") or "Untitled audio"
        sub_parts = []
        if row.get("duration"):
            sub_parts.append(f"Duration: {row.get('duration')}")
        if row.get("link"):
            sub_parts.append(row.get("link"))
        return main, " · ".join(sub_parts)

    main = row.get("details") or "Other task"
    sub = f"{files} file{'s' if files != 1 else ''}" if files else ""
    return main, sub


def render_stats(df: pd.DataFrame) -> None:
    records = len(df)
    completed = int((df["status"] == "Completed").sum()) if not df.empty else 0
    summaries = int((df["project"] == "Summaries").sum()) if not df.empty else 0
    total_wc = int(df["word_count"].sum()) if not df.empty else 0
    files = sum(file_count(items) for items in df["source_files_list"]) if not df.empty else 0

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-card"><div class="metric-label">Total Records</div><div class="metric-value">{records:,}</div></div>
            <div class="metric-card"><div class="metric-label">Completed</div><div class="metric-value">{completed:,}</div></div>
            <div class="metric-card"><div class="metric-label">Summaries</div><div class="metric-value">{summaries:,}</div></div>
            <div class="metric-card"><div class="metric-label">Total Word Count</div><div class="metric-value">{total_wc:,}</div></div>
            <div class="metric-card"><div class="metric-label">Files</div><div class="metric-value">{files:,}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_records_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.markdown(
            "<div class='empty-box'>No records found for this selection.</div>",
            unsafe_allow_html=True,
        )
        return

    rows = []
    for _, row in df.iterrows():
        main, sub = build_details(row)
        row_date = row["task_date"].strftime("%b %d, %Y") if pd.notna(row["task_date"]) else ""
        wc_value = f"{int(row['word_count']):,}" if int(row.get("word_count") or 0) else ""
        rows.append(
            f"""
            <tr>
                <td>{escape(row_date)}</td>
                <td><span class="tag tag-purple">{escape(row['project'])}</span></td>
                <td><div class="detail-main">{escape(main)}</div><div class="detail-sub">{escape(sub)}</div></td>
                <td><span class="tag tag-filled">{escape(row['status'])}</span></td>
                <td>{escape(wc_value)}</td>
            </tr>
            """
        )

    st.markdown(
        f"""
        <table class="rawi-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Project</th>
                    <th>Details</th>
                    <th>Status</th>
                    <th>WC</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def render_summary_table(df: pd.DataFrame) -> None:
    if df.empty:
        st.markdown(
            "<div class='empty-box'>No report data for these filters.</div>",
            unsafe_allow_html=True,
        )
        return

    grouped = (
        df.groupby(["member", "project"], dropna=False)
        .agg(Records=("id", "count"), Word_Count=("word_count", "sum"))
        .reset_index()
        .sort_values(["member", "project"])
    )

    rows = []
    for _, row in grouped.iterrows():
        rows.append(
            f"""
            <tr>
                <td>{escape(row['member'])}</td>
                <td><span class="tag tag-purple">{escape(row['project'])}</span></td>
                <td>{int(row['Records']):,}</td>
                <td>{int(row['Word_Count']):,}</td>
            </tr>
            """
        )

    st.markdown(
        f"""
        <table class="rawi-table">
            <thead>
                <tr>
                    <th>Member</th>
                    <th>Project</th>
                    <th>Records</th>
                    <th>Word Count</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="page-kicker">Rawi Team Performance</div>
        <div class="page-title">{escape(title)}</div>
        <div class="page-subtitle">{escape(subtitle)}</div>
        """,
        unsafe_allow_html=True,
    )


def sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand-row">
                <div class="brand-mark">R</div>
                <div>
                    <div class="brand-title">Rawi</div>
                    <div class="brand-subtitle">Team Performance</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div class='side-label'>Navigation</div>", unsafe_allow_html=True)
        for page in ["Team Details", "Upload", "Reports"]:
            if st.session_state.page == page:
                st.markdown(f"<div class='sidebar-active'>{page}</div>", unsafe_allow_html=True)
            else:
                if st.button(page, key=f"nav_{page}"):
                    st.session_state.page = page
                    st.rerun()

        st.markdown("<div class='side-label'>Team Members</div>", unsafe_allow_html=True)
        for member in TEAM_MEMBERS:
            if st.session_state.selected_member == member and st.session_state.page == "Team Details":
                st.markdown(f"<div class='member-active'>{escape(member)}</div>", unsafe_allow_html=True)
            else:
                if st.button(member, key=f"member_{member}"):
                    st.session_state.selected_member = member
                    st.session_state.page = "Team Details"
                    st.rerun()


def upload_page() -> None:
    top_left, top_right = st.columns([5, 1.1])
    with top_left:
        render_page_header(
            "Upload",
            "Add a team record. The fields change based on the selected project type.",
        )
    with top_right:
        st.write("")
        save_clicked = st.button("Save", type="primary", use_container_width=True)

    st.markdown("<div class='form-panel'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Record Details</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>Select the member, date, status and project before adding the task details.</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        member = st.selectbox("Team Member", ["Select member..."] + TEAM_MEMBERS, key="upload_member")
    with col2:
        task_date = st.date_input("Date", value=date.today(), key="upload_date")

    col3, col4 = st.columns(2)
    with col3:
        status = st.selectbox("Status", ["Select status..."] + STATUSES, key="upload_status")
    with col4:
        project = st.selectbox("Project", ["Select project..."] + PROJECTS, key="upload_project")

    summary_name = ""
    link = ""
    word_count = 0
    duration = ""
    details = ""
    uploaded_files = None

    if project == "Summaries":
        st.markdown("<div class='section-title'>Summary Fields</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([2.2, 1])
        with c1:
            summary_name = st.text_input("Summary Name", placeholder="Example: The Secret Garden", key="summary_name")
        with c2:
            word_count = st.number_input("Word Count", min_value=0, step=1, value=0, key="summary_wc")
        link = st.text_input("Link", placeholder="Paste the summary link", key="summary_link")

    elif project == "Audio":
        st.markdown("<div class='section-title'>Audio Fields</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([2.2, 1])
        with c1:
            summary_name = st.text_input("Summary Name", placeholder="Example: The Secret Garden Audio", key="audio_name")
        with c2:
            duration = st.text_input("Duration", placeholder="Example: 12 min", key="audio_duration")
        link = st.text_input("Link", placeholder="Paste the audio/source link", key="audio_link")

    elif project == "Other Tasks":
        st.markdown("<div class='section-title'>Other Task Fields</div>", unsafe_allow_html=True)
        details = st.text_area(
            "Details",
            placeholder="Write task details, notes, or what needs review.",
            height=150,
            key="other_details",
        )
        uploaded_files = st.file_uploader(
            "Upload File or Image",
            type=["png", "jpg", "jpeg", "webp", "pdf", "docx", "xlsx", "csv", "txt"],
            accept_multiple_files=True,
            key="other_uploads",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    if save_clicked:
        errors = []
        if member == "Select member...":
            errors.append("Pick the team member name.")
        if status == "Select status...":
            errors.append("Pick the status.")
        if project == "Select project...":
            errors.append("Pick the project type.")

        if project == "Summaries":
            if not summary_name.strip():
                errors.append("Write the summary name.")
            if not link.strip():
                errors.append("Add the link.")
            if int(word_count or 0) <= 0:
                errors.append("Add the word count.")
        elif project == "Audio":
            if not summary_name.strip():
                errors.append("Write the summary name.")
            if not link.strip():
                errors.append("Add the link.")
            if not duration.strip():
                errors.append("Add the duration.")
        elif project == "Other Tasks":
            if not details.strip() and not uploaded_files:
                errors.append("Write details or upload a file/image.")

        if errors:
            for error in errors:
                st.error(error)
        else:
            insert_record(
                task_date=task_date,
                member=member,
                status=status,
                project=project,
                summary_name=summary_name,
                link=link,
                word_count=word_count,
                duration=duration,
                details=details,
                uploaded_files=uploaded_files,
            )
            st.session_state.selected_member = member
            st.success("Record saved successfully.")


def manage_records(df: pd.DataFrame) -> None:
    if df.empty:
        return

    st.write("")
    with st.expander("Manage records"):
        for _, row in df.iterrows():
            main, _ = build_details(row)
            with st.container():
                st.markdown(
                    f"**{escape(row['task_date'])} · {escape(row['project'])} · {escape(main)}**"
                )
                edit_col1, edit_col2 = st.columns(2)
                with edit_col1:
                    new_status = st.selectbox(
                        "Status",
                        STATUSES,
                        index=STATUSES.index(row["status"]) if row["status"] in STATUSES else 0,
                        key=f"edit_status_{row['id']}",
                    )
                    new_summary_name = st.text_input(
                        "Title / Summary Name",
                        value=row["summary_name"] or "",
                        key=f"edit_name_{row['id']}",
                    )
                    new_wc = st.number_input(
                        "WC",
                        min_value=0,
                        step=1,
                        value=int(row["word_count"] or 0),
                        key=f"edit_wc_{row['id']}",
                    )
                with edit_col2:
                    new_link = st.text_input(
                        "Link",
                        value=row["link"] or "",
                        key=f"edit_link_{row['id']}",
                    )
                    new_duration = st.text_input(
                        "Duration",
                        value=row["duration"] or "",
                        key=f"edit_duration_{row['id']}",
                    )
                    new_details = st.text_area(
                        "Details",
                        value=row["details"] or "",
                        key=f"edit_details_{row['id']}",
                    )

                files = row.get("source_files_list", [])
                if files:
                    st.markdown("**Files**")
                    for file_info in files:
                        path = Path(file_info.get("path", ""))
                        st.write(f"{file_info.get('name')} · {round((file_info.get('size', 0) or 0) / 1024, 1)} KB")
                        if path.exists():
                            if str(file_info.get("type", "")).startswith("image"):
                                st.image(str(path), width=320)
                            with open(path, "rb") as handle:
                                st.download_button(
                                    f"Download {file_info.get('name')}",
                                    data=handle.read(),
                                    file_name=file_info.get("name"),
                                    key=f"download_{row['id']}_{file_info.get('name')}",
                                )

                action_col1, action_col2 = st.columns([1, 1])
                with action_col1:
                    if st.button("Save Changes", key=f"save_{row['id']}", use_container_width=True):
                        update_record(
                            record_id=row["id"],
                            status=new_status,
                            summary_name=new_summary_name,
                            link=new_link,
                            word_count=new_wc,
                            duration=new_duration,
                            details=new_details,
                        )
                        st.success("Record updated.")
                        st.rerun()
                with action_col2:
                    if st.button("Delete", key=f"delete_{row['id']}", use_container_width=True):
                        delete_record(row["id"])
                        st.success("Record deleted.")
                        st.rerun()


def team_details_page(df: pd.DataFrame) -> None:
    selected_member = st.session_state.selected_member

    header_col, filter_col = st.columns([4, 1.2])
    with header_col:
        render_page_header(
            "Team Details",
            f"Showing records for {selected_member}. Click another name in the sidebar to switch members.",
        )
    with filter_col:
        date_filter = st.selectbox("Date", DATE_FILTERS, index=0, key="team_date_filter")

    member_df = df[df["member"] == selected_member].copy() if not df.empty else df
    member_df = apply_date_filter(member_df, date_filter)

    render_stats(member_df)
    render_records_table(member_df)
    manage_records(member_df)

    if not member_df.empty:
        export_df = member_df[
            ["task_date", "member", "status", "project", "summary_name", "link", "word_count", "duration", "details"]
        ].copy()
        st.download_button(
            "Download Member CSV",
            data=export_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{selected_member.replace(' ', '_')}_records.csv",
            mime="text/csv",
        )


def reports_page(df: pd.DataFrame) -> None:
    render_page_header(
        "Reports",
        "Filter records and review totals grouped by member and project.",
    )

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    with filter_col1:
        date_filter = st.selectbox("Date", DATE_FILTERS, index=0, key="report_date_filter")
    with filter_col2:
        selected_member = st.selectbox("Member", ["All Members"] + TEAM_MEMBERS, key="report_member")
    with filter_col3:
        selected_project = st.selectbox("Project", ["All Projects"] + PROJECTS, key="report_project")
    with filter_col4:
        selected_status = st.selectbox("Status", ["All Statuses"] + STATUSES, key="report_status")

    report_df = apply_date_filter(df, date_filter)
    if selected_member != "All Members":
        report_df = report_df[report_df["member"] == selected_member].copy()
    if selected_project != "All Projects":
        report_df = report_df[report_df["project"] == selected_project].copy()
    if selected_status != "All Statuses":
        report_df = report_df[report_df["status"] == selected_status].copy()

    render_stats(report_df)
    render_summary_table(report_df)

    st.write("")
    st.markdown("<div class='section-title'>Filtered Records</div>", unsafe_allow_html=True)
    render_records_table(report_df)

    if not report_df.empty:
        export_df = report_df[
            ["task_date", "member", "status", "project", "summary_name", "link", "word_count", "duration", "details"]
        ].copy()
        st.download_button(
            "Download Report CSV",
            data=export_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="rawi_report.csv",
            mime="text/csv",
        )


def main() -> None:
    inject_css()
    init_state()
    init_db()
    sidebar()
    df = load_records()

    if st.session_state.page == "Team Details":
        team_details_page(df)
    elif st.session_state.page == "Upload":
        upload_page()
    elif st.session_state.page == "Reports":
        reports_page(df)


if __name__ == "__main__":
    main()
