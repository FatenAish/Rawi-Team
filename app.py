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

# Updated statuses based on request
STATUSES = ["Completed", "In Progress", "Uploaded", "Review"]
PROJECTS = ["Summaries", "Audio", "Other Tasks"]

STATUS_COLORS = {
    "Completed": "#10b981",     # Green
    "In Progress": "#3b82f6",   # Blue
    "Uploaded": "#f59e0b",      # Orange
    "Review": "#8b5cf6",        # Purple
}

# Config
st.set_page_config(page_title=APP_TITLE, page_icon="🟣", layout="wide", initial_sidebar_state="expanded")

def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f9fafb;
            --border: #e5e7eb;
            --text: #111827;
            --muted: #6b7280;
            --purple: #8b5cf6;
            --purple-dark: #7c3aed;
            --purple-light: #ede9fe;
        }

        .stApp {
            background: var(--bg);
        }

        h1, h2, h3, p, div, span, label {
            font-family: Inter, -apple-system, sans-serif;
        }

        .page-title {
            font-size: 28px;
            font-weight: 800;
            color: var(--text);
            letter-spacing: -0.02em;
            margin-bottom: 24px;
        }

        .section-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }

        /* Metric Cards */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }

        .metric-box {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
            border-top: 4px solid var(--purple-light);
        }

        .metric-label {
            color: var(--muted);
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .metric-value {
            color: var(--text);
            font-size: 26px;
            font-weight: 800;
            margin-top: 4px;
        }

        /* Sidebar Brand & Labels */
        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 20px;
            font-weight: 800;
            color: var(--text);
            margin-bottom: 30px;
            padding: 0 10px;
        }

        .sidebar-logo {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            background: var(--purple);
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }

        .sidebar-label {
            color: var(--muted);
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin: 20px 0 8px 10px;
        }

        /* Buttons Styling Overrides */
        div[data-testid="stSidebar"] div[data-testid="stButton"] > button {
            width: 100%;
            justify-content: flex-start;
            border: none;
            background: transparent;
            font-weight: 600;
            color: var(--muted);
            padding: 8px 16px;
            border-radius: 8px;
        }

        div[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
            background: #f3f4f6;
            color: var(--text);
        }

        /* Primary Button Override for Theme */
        .stButton > button[kind="primary"] {
            background-color: var(--purple) !important;
            color: white !important;
            border-color: var(--purple) !important;
            font-weight: 600 !important;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: var(--purple-dark) !important;
            border-color: var(--purple-dark) !important;
        }

        /* Status Pill */
        .status-pill {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            color: white;
        }
        
        div[data-testid="stDataFrame"] {
            border-radius: 12px;
            border: 1px solid var(--border);
            overflow: hidden;
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
    if "save_trigger" not in st.session_state:
        st.session_state.save_trigger = False


def init_db() -> None:
    required_columns = {
        "id": "TEXT PRIMARY KEY",
        "created_at": "TEXT NOT NULL",
        "updated_at": "TEXT",
        "task_date": "TEXT",
        "member": "TEXT NOT NULL",
        "status": "TEXT NOT NULL",
        "project": "TEXT",
        "summary_name": "TEXT",
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

        existing = {row[1] for row in conn.execute("PRAGMA table_info(performance_records)").fetchall()}
        for column, col_type in required_columns.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE performance_records ADD COLUMN {column} {col_type}")
        conn.commit()


def safe_json_loads(value):
    if not value:
        return []
    try:
        loaded = json.loads(value)
        return loaded if isinstance(loaded, list) else []
    except Exception:
        return []


def load_records() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            "SELECT * FROM performance_records ORDER BY task_date DESC, created_at DESC",
            conn,
        )

    expected_cols = [
        "id", "created_at", "updated_at", "task_date", "member", "status", "project", 
        "summary_name", "link", "word_count", "duration", "details", "source_files",
    ]

    if df.empty:
        return pd.DataFrame(columns=expected_cols + ["source_files_list"])

    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")
    df["task_date"] = pd.to_datetime(df["task_date"], errors="coerce").dt.date
    df["source_files_list"] = df["source_files"].apply(safe_json_loads)
    df["word_count"] = pd.to_numeric(df["word_count"], errors="coerce").fillna(0).astype(int)

    return df[expected_cols + ["source_files_list"]]


def save_uploaded_files(record_id: str, uploaded_files) -> list[dict]:
    saved = []
    if not uploaded_files:
        return saved
    folder = UPLOAD_DIR / record_id
    folder.mkdir(parents=True, exist_ok=True)
    for uploaded_file in uploaded_files:
        safe_name = uploaded_file.name.replace("/", "_").replace("\\", "_")
        output_path = folder / safe_name
        output_path.write_bytes(uploaded_file.getbuffer())
        saved.append(
            {
                "name": uploaded_file.name,
                "path": str(output_path),
                "type": uploaded_file.type or "file",
                "size": uploaded_file.size,
            }
        )
    return saved


def insert_record(*, task_date: date, member: str, status: str, project: str, summary_name: str = "", link: str = "", word_count: int = 0, duration: str = "", details: str = "", uploaded_files=None) -> str:
    record_id = str(uuid.uuid4())
    files = save_uploaded_files(record_id, uploaded_files)
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO performance_records
            (id, created_at, updated_at, task_date, member, status, project, summary_name, link,
             word_count, duration, details, source_files)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id, now, now, task_date.isoformat(), member, status, project, summary_name.strip(), 
                link.strip(), int(word_count or 0), duration.strip(), details.strip(), json.dumps(files, ensure_ascii=False)
            ),
        )
        conn.commit()
    return record_id


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-logo">R</div>
                <div>Rawi Team</div>
            </div>
            """, unsafe_allow_html=True
        )

        st.markdown('<div class="sidebar-label">Navigation</div>', unsafe_allow_html=True)
        for page in ["Team Details", "Upload", "Reports"]:
            is_active = st.session_state.page == page
            # Use primary kind if active so it inherits the purple theme
            if st.button(page, key=f"nav_{page}", type="primary" if is_active else "secondary", use_container_width=True):
                st.session_state.page = page
                st.rerun()

        st.markdown('<div class="sidebar-label">Team Members</div>', unsafe_allow_html=True)
        for member in TEAM_MEMBERS:
            # Highlight selected member only if we are on the Team Details page (or globally)
            is_active_member = st.session_state.selected_member == member and st.session_state.page == "Team Details"
            if st.button(member, key=f"mem_{member}", type="primary" if is_active_member else "secondary", use_container_width=True):
                st.session_state.selected_member = member
                st.session_state.page = "Team Details"
                st.rerun()


def display_stat_cards(df: pd.DataFrame):
    total_records = len(df)
    completed = int((df["status"] == "Completed").sum()) if not df.empty else 0
    summaries = int((df["project"] == "Summaries").sum()) if not df.empty else 0
    total_wc = int(df["word_count"].sum()) if not df.empty else 0
    total_files = sum(len(x) for x in df["source_files_list"]) if not df.empty else 0

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-box"><div class="metric-label">Records</div><div class="metric-value">{total_records}</div></div>
            <div class="metric-box"><div class="metric-label">Completed</div><div class="metric-value">{completed}</div></div>
            <div class="metric-box"><div class="metric-label">Summaries</div><div class="metric-value">{summaries}</div></div>
            <div class="metric-box"><div class="metric-label">Total Word Count</div><div class="metric-value">{total_wc:,}</div></div>
            <div class="metric-box"><div class="metric-label">Files Uploaded</div><div class="metric-value">{total_files}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def team_details_page(df: pd.DataFrame) -> None:
    st.markdown(f"<div class='page-title'>{st.session_state.selected_member} — Team Details</div>", unsafe_allow_html=True)
    
    member_df = df[df["member"] == st.session_state.selected_member].copy() if not df.empty else df
    
    display_stat_cards(member_df)

    if member_df.empty:
        st.info(f"No records found for {st.session_state.selected_member}.")
        return

    # Data Table Formatting
    table_df = member_df.copy()
    table_df["Date"] = table_df["task_date"].apply(lambda x: x.strftime("%B %d, %Y") if pd.notna(x) else "")
    table_df["Project"] = table_df["project"].fillna("")
    table_df["Details"] = table_df.apply(lambda r: r["summary_name"] if str(r.get("summary_name") or "").strip() else str(r.get("details") or "")[:80], axis=1)
    table_df["Status"] = table_df["status"].fillna("")
    table_df["WC"] = table_df["word_count"].replace(0, "")

    st.markdown("### Recent Records")
    st.dataframe(
        table_df[["Date", "Project", "Details", "Status", "WC"]],
        hide_index=True,
        use_container_width=True,
        column_config={"WC": st.column_config.NumberColumn("WC", format="%d")},
    )


def upload_page() -> None:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("<div class='page-title'>Upload Task</div>", unsafe_allow_html=True)
    with col2:
        # Save button in the top right
        st.write("") # slight alignment spacer
        save_clicked = st.button("Save Record", type="primary", use_container_width=True)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        member = st.selectbox("Team member", ["Select member..."] + TEAM_MEMBERS, index=TEAM_MEMBERS.index(st.session_state.selected_member) + 1 if st.session_state.selected_member else 0)
    with c2:
        task_date = st.date_input("Date", value=date.today())

    c3, c4 = st.columns(2)
    with c3:
        status = st.selectbox("Status", ["Select status..."] + STATUSES)
    with c4:
        project = st.selectbox("Project Type", ["Select project..."] + PROJECTS)

    st.markdown("<hr style='margin: 20px 0; border-color: #e5e7eb;'>", unsafe_allow_html=True)

    summary_name = ""
    link = ""
    word_count = 0
    duration = ""
    details = ""
    uploaded_files = None

    if project == "Summaries":
        s1, s2 = st.columns([3, 1])
        with s1:
            summary_name = st.text_input("Title")
        with s2:
            word_count = st.number_input("Word Count", min_value=0, step=1, value=0)
        link = st.text_input("Link", placeholder="https://...")

    elif project == "Audio":
        a1, a2 = st.columns([3, 1])
        with a1:
            summary_name = st.text_input("Title")
        with a2:
            duration = st.text_input("Duration", placeholder="00:15:00")
        link = st.text_input("Link", placeholder="https://...")

    elif project == "Other Tasks":
        details = st.text_area("Task Details", height=120)
        uploaded_files = st.file_uploader("Upload File/Image", accept_multiple_files=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    if save_clicked:
        errors = []
        if member == "Select member...": errors.append("Select a team member.")
        if status == "Select status...": errors.append("Select a status.")
        if project == "Select project...": errors.append("Select a project type.")

        if project == "Summaries":
            if not summary_name.strip(): errors.append("Provide a title.")
            if not link.strip(): errors.append("Provide a link.")
        elif project == "Audio":
            if not summary_name.strip(): errors.append("Provide a title.")
            if not duration.strip(): errors.append("Provide a duration.")
        elif project == "Other Tasks":
            if not details.strip() and not uploaded_files: errors.append("Provide details or upload a file.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            insert_record(
                task_date=task_date, member=member, status=status, project=project,
                summary_name=summary_name, link=link, word_count=word_count,
                duration=duration, details=details, uploaded_files=uploaded_files,
            )
            st.success("Task saved successfully.")
            st.session_state.selected_member = member


def reports_page(df: pd.DataFrame) -> None:
    st.markdown("<div class='page-title'>Performance Reports</div>", unsafe_allow_html=True)

    if df.empty:
        st.info("No records available to report.")
        return

    # 4 Filters
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        date_filter = st.selectbox("Date", ["All Time", "Today", "This Week", "This Month"])
    with f2:
        member_filter = st.selectbox("Member", ["All Members"] + TEAM_MEMBERS)
    with f3:
        project_filter = st.selectbox("Project", ["All Projects"] + PROJECTS)
    with f4:
        status_filter = st.selectbox("Status", ["All Statuses"] + STATUSES)

    # Apply date filter conceptually
    report_df = df.copy()
    today = date.today()
    if date_filter == "Today":
        report_df = report_df[report_df["task_date"] == today]
    elif date_filter == "This Week":
        start_of_week = today - timedelta(days=today.weekday())
        report_df = report_df[report_df["task_date"] >= start_of_week]
    elif date_filter == "This Month":
        start_of_month = today.replace(day=1)
        report_df = report_df[report_df["task_date"] >= start_of_month]

    if member_filter != "All Members":
        report_df = report_df[report_df["member"] == member_filter]
    if project_filter != "All Projects":
        report_df = report_df[report_df["project"] == project_filter]
    if status_filter != "All Statuses":
        report_df = report_df[report_df["status"] == status_filter]

    display_stat_cards(report_df)

    st.markdown("### Summary by Member & Project")
    if report_df.empty:
        st.warning("No records match your filters.")
    else:
        grouped = (
            report_df.groupby(["member", "project"], dropna=False)
            .agg(Records=("id", "count"), Word_Count=("word_count", "sum"))
            .reset_index()
            .rename(columns={"member": "Member", "project": "Project", "Word_Count": "Total WC"})
        )
        st.dataframe(grouped, hide_index=True, use_container_width=True)


def main() -> None:
    inject_css()
    init_state()
    init_db()
    df = load_records()

    render_sidebar()

    # Route Pages
    if st.session_state.page == "Team Details":
        team_details_page(df)
    elif st.session_state.page == "Upload":
        upload_page()
    elif st.session_state.page == "Reports":
        reports_page(df)


if __name__ == "__main__":
    main()
