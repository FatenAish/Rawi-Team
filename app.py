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

# Config
st.set_page_config(page_title=APP_TITLE, page_icon="🟢", layout="wide", initial_sidebar_state="expanded")

def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg-main: #faf9f6;
            --bg-sidebar: #ffffff;
            --border-color: #e5e7eb;
            --text-main: #111827;
            --text-muted: #6b7280;
            --green-logo: #186846;
        }

        /* App Background */
        .stApp {
            background: var(--bg-main);
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: var(--bg-sidebar) !important;
            border-right: 1px solid var(--border-color);
        }

        /* Typography */
        h1, h2, h3, p, div, span, label {
            font-family: Inter, -apple-system, sans-serif;
        }

        .page-title {
            font-size: 26px;
            font-weight: 600;
            color: var(--text-main);
            margin-bottom: 4px;
        }
        
        .page-subtitle {
            font-size: 14px;
            color: var(--text-muted);
            margin-bottom: 24px;
        }

        /* Sidebar Brand & Labels */
        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 30px;
            padding: 0 4px;
        }

        .sidebar-logo {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            background: var(--green-logo);
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: 700;
        }

        .sidebar-label {
            color: var(--text-muted);
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin: 20px 0 8px 4px;
        }

        /* Sidebar Buttons Override */
        div[data-testid="stSidebar"] div[data-testid="stButton"] > button {
            width: 100%;
            justify-content: flex-start;
            border: 1px solid var(--border-color);
            background: #ffffff;
            font-weight: 500;
            color: var(--text-main);
            padding: 8px 16px;
            border-radius: 8px;
            margin-bottom: 4px;
        }

        div[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
            background: #f9fafb;
            border-color: #d1d5db;
        }

        /* Active Sidebar Button */
        div[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] {
            background-color: #f3f4f6 !important;
            color: var(--text-main) !important;
            border-color: #d1d5db !important;
            font-weight: 600 !important;
        }
        
        /* Main area Save Button */
        .save-btn-container div[data-testid="stButton"] > button {
            border: 1px solid var(--border-color);
            background: #ffffff;
            color: var(--text-main);
            border-radius: 8px;
            font-weight: 500;
            float: right;
            padding: 4px 16px;
        }
        .save-btn-container div[data-testid="stButton"] > button:hover {
            border-color: #9ca3af;
        }

        /* Input Labels */
        .stSelectbox label, .stDateInput label, .stTextInput label, .stNumberInput label {
            font-size: 11px !important;
            text-transform: uppercase !important;
            color: var(--text-muted) !important;
            letter-spacing: 0.05em !important;
            font-weight: 600 !important;
        }
        
        /* Metric/Report Cards */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .metric-box {
            background: #ffffff;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
        }
        .metric-label {
            color: var(--text-muted);
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .metric-value {
            color: var(--text-main);
            font-size: 24px;
            font-weight: 700;
            margin-top: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
                week_start TEXT,
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
                # Provide a default fallback to avoid constraints failing on existing data
                default_val = "''" if "NOT NULL" in col_type.upper() else "NULL"
                conn.execute(f"ALTER TABLE performance_records ADD COLUMN {column} {col_type} DEFAULT {default_val}")
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
        "id", "created_at", "updated_at", "task_date", "week_start", "member", "status", "project", 
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
    df["week_start"] = pd.to_datetime(df["week_start"], errors="coerce").dt.date
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
    
    task_date_obj = task_date if task_date else date.today()
    task_date_str = task_date_obj.isoformat()
    
    # Calculate the start of the week (Monday)
    week_start_str = (task_date_obj - timedelta(days=task_date_obj.weekday())).isoformat()
    
    word_count_int = int(word_count) if word_count else 0

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO performance_records
            (id, created_at, updated_at, task_date, week_start, member, status, project, summary_name, link,
             word_count, duration, details, source_files)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id, now, now, task_date_str, week_start_str, member, status, project, 
                str(summary_name).strip(), str(link).strip(), word_count_int, 
                str(duration).strip(), str(details).strip(), json.dumps(files, ensure_ascii=False)
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
                <div>
                    <div style="font-weight: 600; font-size: 15px; color: #111827;">Rawi team</div>
                    <div style="font-size: 12px; color: #6b7280;">Performance tracker</div>
                </div>
            </div>
            """, unsafe_allow_html=True
        )

        st.markdown('<div class="sidebar-label">NAVIGATION</div>', unsafe_allow_html=True)
        nav_items = {
            "Team Details": "👥 Team details",
            "Upload": "↑ Upload",
            "Reports": "📊 Reports"
        }
        for page, label in nav_items.items():
            is_active = st.session_state.page == page
            if st.button(label, key=f"nav_{page}", type="primary" if is_active else "secondary", use_container_width=True):
                st.session_state.page = page
                st.rerun()

        st.markdown('<div class="sidebar-label">TEAM MEMBERS</div>', unsafe_allow_html=True)
        for member in TEAM_MEMBERS:
            is_active_member = st.session_state.selected_member == member and st.session_state.page == "Team Details"
            label = f"• {member}"
            if st.button(label, key=f"mem_{member}", type="primary" if is_active_member else "secondary", use_container_width=True):
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
    st.markdown(f"<div class='page-title'>Team details</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='page-subtitle'>Performance records for {st.session_state.selected_member}</div>", unsafe_allow_html=True)
    
    member_df = df[df["member"] == st.session_state.selected_member].copy() if not df.empty else df
    display_stat_cards(member_df)

    if member_df.empty:
        st.info(f"No records found for {st.session_state.selected_member}.")
        return

    table_df = member_df.copy()
    table_df["Date"] = table_df["task_date"].apply(lambda x: x.strftime("%m/%d/%Y") if pd.notna(x) else "")
    table_df["Project"] = table_df["project"].fillna("")
    table_df["Details"] = table_df.apply(lambda r: r["summary_name"] if str(r.get("summary_name") or "").strip() else str(r.get("details") or "")[:80], axis=1)
    table_df["Status"] = table_df["status"].fillna("")
    table_df["WC"] = table_df["word_count"].replace(0, "")

    st.dataframe(
        table_df[["Date", "Project", "Details", "Status", "WC"]],
        hide_index=True,
        use_container_width=True,
        column_config={"WC": st.column_config.NumberColumn("WC", format="%d")},
    )


def upload_page() -> None:
    # Header area
    col_text, col_btn = st.columns([4, 1])
    with col_text:
        st.markdown("<div class='page-title'>Upload task</div>", unsafe_allow_html=True)
        st.markdown("<div class='page-subtitle'>Record a new task for a team member</div>", unsafe_allow_html=True)
    with col_btn:
        st.markdown("<div class='save-btn-container'>", unsafe_allow_html=True)
        save_clicked = st.button("＋ Save task", use_container_width=False)
        st.markdown("</div>", unsafe_allow_html=True)

    # Form Container
    with st.container():
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

        # Dynamic Project Fields
        summary_name = ""
        link = ""
        word_count = 0
        duration = ""
        details = ""
        uploaded_files = None

        if project == "Select project...":
            st.markdown(
                """
                <div style="background-color: #f6f5ef; border-radius: 8px; padding: 30px; text-align: center; color: #4b5563; margin-top: 16px;">
                    <div style="font-size: 20px; margin-bottom: 4px;">↑</div>
                    <div style="font-size: 14px; font-weight: 500;">Select a project to see task fields</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            st.markdown("<hr style='margin: 20px 0; border-color: #e5e7eb;'>", unsafe_allow_html=True)
            
            if project == "Summaries":
                s1, s2 = st.columns([3, 1])
                with s1:
                    summary_name = st.text_input("TITLE")
                with s2:
                    word_count = st.number_input("WORD COUNT", min_value=0, step=1, value=0)
                link = st.text_input("LINK", placeholder="https://...")

            elif project == "Audio":
                a1, a2 = st.columns([3, 1])
                with a1:
                    summary_name = st.text_input("TITLE")
                with a2:
                    duration = st.text_input("DURATION", placeholder="00:15:00")
                link = st.text_input("LINK", placeholder="https://...")

            elif project == "Other Tasks":
                details = st.text_area("TASK DETAILS", height=120)
                uploaded_files = st.file_uploader("UPLOAD FILE/IMAGE", accept_multiple_files=True)

    # Save Logic
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
            try:
                insert_record(
                    task_date=task_date, member=member, status=status, project=project,
                    summary_name=summary_name, link=link, word_count=word_count,
                    duration=duration, details=details, uploaded_files=uploaded_files,
                )
                st.success("Task saved successfully.")
                st.session_state.selected_member = member
            except sqlite3.IntegrityError as e:
                st.error(f"Database Integrity Error: {e}. Please ensure all required constraints are met.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")


def reports_page(df: pd.DataFrame) -> None:
    st.markdown("<div class='page-title'>Performance Reports</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Filter and view overall team metrics</div>", unsafe_allow_html=True)

    if df.empty:
        st.info("No records available to report.")
        return

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        date_filter = st.selectbox("DATE", ["All Time", "Today", "This Week", "This Month"])
    with f2:
        member_filter = st.selectbox("MEMBER", ["All Members"] + TEAM_MEMBERS)
    with f3:
        project_filter = st.selectbox("PROJECT", ["All Projects"] + PROJECTS)
    with f4:
        status_filter = st.selectbox("STATUS", ["All Statuses"] + STATUSES)

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

    if st.session_state.page == "Team Details":
        team_details_page(df)
    elif st.session_state.page == "Upload":
        upload_page()
    elif st.session_state.page == "Reports":
        reports_page(df)

if __name__ == "__main__":
    main()
