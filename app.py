import html
import json
import sqlite3
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

APP_TITLE = "Rawi Team Performance"
DB_PATH = Path("rawi_team_performance_purple_clean.db")
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

PURPLE = "#6D28D9"
PURPLE_DARK = "#4C1D95"
PURPLE_SOFT = "#F3E8FF"
BORDER = "#E5E7EB"
TEXT = "#111827"
MUTED = "#6B7280"

st.set_page_config(page_title=APP_TITLE, page_icon="R", layout="wide")


def esc(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --purple: {PURPLE};
            --purple-dark: {PURPLE_DARK};
            --purple-soft: {PURPLE_SOFT};
            --bg: #F8F7FC;
            --card: #FFFFFF;
            --border: {BORDER};
            --text: {TEXT};
            --muted: {MUTED};
        }}

        .stApp {{
            background: var(--bg);
        }}

        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1420px;
        }}

        h1, h2, h3, p, div, span, label {{
            font-family: Inter, Arial, sans-serif;
        }}

        [data-testid="stSidebar"] {{
            background: #FFFFFF;
            border-right: 1px solid var(--border);
            min-width: 285px;
        }}

        [data-testid="stSidebar"] > div:first-child {{
            padding-top: 1.35rem;
        }}

        .brand-wrap {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 4px 4px 22px 4px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 18px;
        }}

        .brand-logo {{
            width: 44px;
            height: 44px;
            border-radius: 13px;
            background: linear-gradient(135deg, var(--purple), #A855F7);
            color: #FFFFFF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 22px;
            box-shadow: 0 8px 18px rgba(109, 40, 217, 0.22);
        }}

        .brand-title {{
            color: var(--text);
            font-weight: 850;
            font-size: 18px;
            line-height: 1.1;
        }}

        .brand-subtitle {{
            color: var(--muted);
            font-size: 12px;
            margin-top: 2px;
        }}

        .sidebar-label {{
            color: var(--muted);
            font-weight: 800;
            font-size: 11px;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin: 18px 0 8px 4px;
        }}

        .sidebar-active {{
            background: var(--purple-soft);
            color: var(--purple-dark);
            border: 1px solid #DDD6FE;
            border-left: 5px solid var(--purple);
            border-radius: 12px;
            padding: 11px 13px;
            font-weight: 850;
            margin-bottom: 7px;
        }}

        .member-active {{
            background: var(--purple-soft);
            color: var(--purple-dark);
            border: 1px solid #DDD6FE;
            border-left: 5px solid var(--purple);
            border-radius: 12px;
            padding: 10px 13px;
            font-weight: 850;
            margin-bottom: 7px;
        }}

        div[data-testid="stSidebar"] div[data-testid="stButton"] button {{
            width: 100%;
            justify-content: flex-start;
            border-radius: 12px;
            border: 1px solid transparent;
            background: #FFFFFF;
            color: var(--text);
            font-weight: 700;
            padding: 10px 13px;
            margin-bottom: 4px;
        }}

        div[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{
            background: #F9FAFB;
            border-color: var(--border);
            color: var(--purple-dark);
        }}

        .page-head {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 18px;
            margin-bottom: 22px;
        }}

        .page-title {{
            color: var(--text);
            font-size: 34px;
            font-weight: 900;
            line-height: 1.1;
            letter-spacing: -0.04em;
            margin: 0;
        }}

        .page-subtitle {{
            color: var(--muted);
            font-size: 14px;
            margin-top: 6px;
        }}

        .save-top-note {{
            border: 1px solid var(--border);
            background: #FFFFFF;
            border-radius: 14px;
            padding: 10px 14px;
            color: var(--muted);
            font-size: 13px;
            margin-top: 4px;
        }}

        .card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 18px;
            box-shadow: 0 2px 10px rgba(17, 24, 39, 0.035);
        }}

        .form-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 24px;
            max-width: 850px;
            box-shadow: 0 2px 10px rgba(17, 24, 39, 0.035);
        }}

        .form-section-title {{
            color: var(--purple-dark);
            font-size: 12px;
            font-weight: 900;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin: 10px 0 12px 0;
        }}

        .upload-placeholder {{
            background: #FAF5FF;
            border: 1px dashed #C4B5FD;
            border-radius: 16px;
            padding: 30px;
            text-align: center;
            color: var(--purple-dark);
            font-weight: 700;
        }}

        .stButton > button[kind="primary"] {{
            background: var(--purple) !important;
            color: #FFFFFF !important;
            border-color: var(--purple) !important;
            border-radius: 12px !important;
            font-weight: 850 !important;
            min-height: 42px;
        }}

        .stButton > button[kind="primary"]:hover {{
            background: var(--purple-dark) !important;
            border-color: var(--purple-dark) !important;
        }}

        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stDateInput"] input,
        textarea {{
            border-radius: 12px !important;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(5, minmax(130px, 1fr));
            gap: 14px;
            margin: 18px 0;
        }}

        .stat-card {{
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 16px 18px;
            box-shadow: 0 2px 10px rgba(17, 24, 39, 0.03);
        }}

        .stat-label {{
            color: var(--muted);
            font-size: 11px;
            font-weight: 850;
            letter-spacing: .06em;
            text-transform: uppercase;
        }}

        .stat-value {{
            color: var(--text);
            font-size: 31px;
            font-weight: 950;
            line-height: 1;
            margin-top: 10px;
            letter-spacing: -0.04em;
        }}

        .table-card {{
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(17, 24, 39, 0.035);
        }}

        .table-top {{
            background: #FFFFFF;
            border-bottom: 1px solid var(--border);
            padding: 18px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
        }}

        .table-title {{
            font-weight: 900;
            font-size: 18px;
            color: var(--text);
        }}

        .table-subtitle {{
            color: var(--muted);
            font-size: 13px;
        }}

        .rawi-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}

        .rawi-table th {{
            background: #FAFAFB;
            color: #374151;
            text-align: left;
            font-size: 11px;
            letter-spacing: .07em;
            text-transform: uppercase;
            font-weight: 900;
            padding: 13px 14px;
            border-bottom: 1px solid var(--border);
        }}

        .rawi-table td {{
            padding: 13px 14px;
            border-bottom: 1px solid #F0F2F5;
            color: var(--text);
            vertical-align: top;
        }}

        .rawi-table tr:hover td {{
            background: #FBFAFF;
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: 850;
            white-space: nowrap;
        }}

        .badge-project {{
            background: var(--purple-soft);
            color: var(--purple-dark);
            border: 1px solid #DDD6FE;
        }}

        .badge-status {{
            background: var(--purple);
            color: #FFFFFF;
        }}

        .detail-link {{
            color: var(--purple-dark);
            font-weight: 800;
            text-decoration: none;
        }}

        .detail-link:hover {{
            text-decoration: underline;
        }}

        .empty-state {{
            background: #FFFFFF;
            border: 1px dashed #C4B5FD;
            border-radius: 16px;
            padding: 28px;
            color: var(--muted);
            text-align: center;
            margin-top: 16px;
        }}

        .filters-card {{
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 18px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    if "page" not in st.session_state:
        st.session_state.page = "Upload"
    if "selected_member" not in st.session_state:
        st.session_state.selected_member = TEAM_MEMBERS[0]


def sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand-wrap">
                <div class="brand-logo">R</div>
                <div>
                    <div class="brand-title">Rawi team</div>
                    <div class="brand-subtitle">Performance tracker</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div class='sidebar-label'>Navigation</div>", unsafe_allow_html=True)
        for page in ["Team Details", "Upload", "Reports"]:
            if st.session_state.page == page:
                st.markdown(f"<div class='sidebar-active'>{esc(page)}</div>", unsafe_allow_html=True)
            else:
                if st.button(page, key=f"nav_{page}"):
                    st.session_state.page = page
                    st.rerun()

        st.markdown("<div class='sidebar-label'>Team members</div>", unsafe_allow_html=True)
        for member in TEAM_MEMBERS:
            if st.session_state.selected_member == member:
                st.markdown(f"<div class='member-active'>• {esc(member)}</div>", unsafe_allow_html=True)
            else:
                if st.button(f"• {member}", key=f"member_{member}"):
                    st.session_state.selected_member = member
                    st.session_state.page = "Team Details"
                    st.rerun()


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id TEXT PRIMARY KEY,
                created_at TEXT,
                updated_at TEXT,
                task_date TEXT,
                member TEXT,
                status TEXT,
                project TEXT,
                title TEXT,
                link TEXT,
                word_count INTEGER DEFAULT 0,
                duration TEXT,
                details TEXT,
                files_json TEXT
            )
            """
        )
        conn.commit()


def json_load(value) -> list:
    if not value:
        return []
    try:
        data = json.loads(value)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def load_records() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM records ORDER BY task_date DESC, created_at DESC", conn)

    cols = [
        "id", "created_at", "updated_at", "task_date", "member", "status", "project",
        "title", "link", "word_count", "duration", "details", "files_json",
    ]
    if df.empty:
        return pd.DataFrame(columns=cols + ["files"])

    for col in cols:
        if col not in df.columns:
            df[col] = None

    df["task_date"] = pd.to_datetime(df["task_date"], errors="coerce").dt.date
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")
    df["word_count"] = pd.to_numeric(df["word_count"], errors="coerce").fillna(0).astype(int)
    df["files"] = df["files_json"].apply(json_load)
    return df[cols + ["files"]]


def save_files(record_id: str, uploaded_files) -> list[dict]:
    if not uploaded_files:
        return []

    folder = UPLOAD_DIR / record_id
    folder.mkdir(parents=True, exist_ok=True)
    saved = []

    for uploaded_file in uploaded_files:
        safe_name = uploaded_file.name.replace("/", "_").replace("\\", "_")
        path = folder / safe_name
        path.write_bytes(uploaded_file.getbuffer())
        saved.append(
            {
                "name": uploaded_file.name,
                "path": str(path),
                "type": uploaded_file.type or "file",
                "size": uploaded_file.size,
            }
        )

    return saved


def insert_record(
    *,
    task_date: date,
    member: str,
    status: str,
    project: str,
    title: str = "",
    link: str = "",
    word_count: int = 0,
    duration: str = "",
    details: str = "",
    uploaded_files=None,
) -> str:
    record_id = str(uuid.uuid4())
    now = datetime.now().isoformat(timespec="seconds")
    files = save_files(record_id, uploaded_files)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO records
            (id, created_at, updated_at, task_date, member, status, project, title, link, word_count, duration, details, files_json)
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
                title.strip(),
                link.strip(),
                int(word_count or 0),
                duration.strip(),
                details.strip(),
                json.dumps(files, ensure_ascii=False),
            ),
        )
        conn.commit()

    return record_id


def delete_record(record_id: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
        conn.commit()


def update_record(record_id: str, status: str, title: str, link: str, word_count: int, duration: str, details: str) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE records
            SET updated_at = ?, status = ?, title = ?, link = ?, word_count = ?, duration = ?, details = ?
            WHERE id = ?
            """,
            (now, status, title.strip(), link.strip(), int(word_count or 0), duration.strip(), details.strip(), record_id),
        )
        conn.commit()


def apply_date_filter(df: pd.DataFrame, label: str, start=None, end=None) -> pd.DataFrame:
    if df.empty or label == "All time":
        return df

    today = date.today()
    if label == "Today":
        start = end = today
    elif label == "This week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
    elif label == "Last week":
        this_week = today - timedelta(days=today.weekday())
        start = this_week - timedelta(days=7)
        end = start + timedelta(days=6)
    elif label == "This month":
        start = today.replace(day=1)
        end = today
    elif label == "Custom range":
        if start is None or end is None:
            return df

    return df[(df["task_date"] >= start) & (df["task_date"] <= end)]


def stat_cards(df: pd.DataFrame) -> None:
    records = len(df)
    completed = int((df["status"] == "Completed").sum()) if not df.empty else 0
    summaries = int((df["project"] == "Summaries").sum()) if not df.empty else 0
    wc = int(df["word_count"].sum()) if not df.empty else 0
    files = sum(len(x) for x in df["files"]) if not df.empty else 0

    st.markdown(
        f"""
        <div class="stats-grid">
            <div class="stat-card"><div class="stat-label">Records</div><div class="stat-value">{records:,}</div></div>
            <div class="stat-card"><div class="stat-label">Completed</div><div class="stat-value">{completed:,}</div></div>
            <div class="stat-card"><div class="stat-label">Summaries</div><div class="stat-value">{summaries:,}</div></div>
            <div class="stat-card"><div class="stat-label">Total Word Count</div><div class="stat-value">{wc:,}</div></div>
            <div class="stat-card"><div class="stat-label">Files</div><div class="stat-value">{files:,}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def row_details(row) -> str:
    title = esc(row.get("title") or "")
    details = esc(row.get("details") or "")
    link = esc(row.get("link") or "")
    duration = esc(row.get("duration") or "")
    files = row.get("files") or []

    parts = []
    if title:
        parts.append(f"<strong>{title}</strong>")
    if details:
        parts.append(f"<div style='color:#4B5563;margin-top:3px;'>{details}</div>")
    if duration:
        parts.append(f"<div style='color:#6B7280;margin-top:3px;'>Duration: {duration}</div>")
    if link:
        parts.append(f"<div style='margin-top:5px;'><a class='detail-link' href='{link}' target='_blank'>Open link</a></div>")
    if files:
        parts.append(f"<div style='color:#6B7280;margin-top:3px;'>{len(files)} file(s)</div>")
    return "".join(parts) if parts else "—"


def render_records_table(df: pd.DataFrame, title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="table-card">
            <div class="table-top">
                <div>
                    <div class="table-title">{esc(title)}</div>
                    <div class="table-subtitle">{esc(subtitle)}</div>
                </div>
            </div>
            <table class="rawi-table">
                <thead>
                    <tr>
                        <th style="width:120px;">Date</th>
                        <th style="width:130px;">Project</th>
                        <th>Details</th>
                        <th style="width:130px;">Status</th>
                        <th style="width:90px;">WC</th>
                    </tr>
                </thead>
                <tbody>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.markdown(
            """
                    <tr><td colspan="5" style="text-align:center;color:#6B7280;padding:28px;">No records found.</td></tr>
                </tbody>
            </table>
        </div>
            """,
            unsafe_allow_html=True,
        )
        return

    rows_html = []
    for _, row in df.iterrows():
        task_date = row["task_date"].strftime("%b %d, %Y") if pd.notna(row["task_date"]) else ""
        project = esc(row.get("project") or "")
        status = esc(row.get("status") or "")
        wc = int(row.get("word_count") or 0)
        wc_text = f"{wc:,}" if wc else ""
        rows_html.append(
            f"""
            <tr>
                <td>{esc(task_date)}</td>
                <td><span class="badge badge-project">{project}</span></td>
                <td>{row_details(row)}</td>
                <td><span class="badge badge-status">{status}</span></td>
                <td>{wc_text}</td>
            </tr>
            """
        )

    st.markdown("".join(rows_html) + "</tbody></table></div>", unsafe_allow_html=True)


def page_header(title: str, subtitle: str, right_note: str = "") -> None:
    st.markdown(
        f"""
        <div class="page-head">
            <div>
                <h1 class="page-title">{esc(title)}</h1>
                <div class="page-subtitle">{esc(subtitle)}</div>
            </div>
            {f'<div class="save-top-note">{esc(right_note)}</div>' if right_note else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def upload_page() -> None:
    page_header("Upload task", "Record a new task for a team member.", "+ Save task is below")

    st.markdown("<div class='form-card'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        member = st.selectbox("TEAM MEMBER", ["Select member..."] + TEAM_MEMBERS)
    with c2:
        task_date = st.date_input("DATE", value=date.today())

    c3, c4 = st.columns(2)
    with c3:
        status = st.selectbox("STATUS", ["Select status..."] + STATUSES)
    with c4:
        project = st.selectbox("PROJECT", ["Select project..."] + PROJECTS)

    title = ""
    link = ""
    word_count = 0
    duration = ""
    details = ""
    uploaded_files = None

    if project == "Select project...":
        st.markdown("<div class='upload-placeholder'>Select a project to see task fields</div>", unsafe_allow_html=True)
    elif project == "Summaries":
        st.markdown("<div class='form-section-title'>Summary details</div>", unsafe_allow_html=True)
        s1, s2 = st.columns([2, 1])
        with s1:
            title = st.text_input("TITLE", placeholder="Summary name")
        with s2:
            word_count = st.number_input("WC", min_value=0, step=1, value=0)
        link = st.text_input("LINK", placeholder="Paste link")
    elif project == "Audio":
        st.markdown("<div class='form-section-title'>Audio details</div>", unsafe_allow_html=True)
        a1, a2 = st.columns([2, 1])
        with a1:
            title = st.text_input("TITLE", placeholder="Audio / summary name")
        with a2:
            duration = st.text_input("DURATION", placeholder="Example: 12 min or 00:12:30")
        link = st.text_input("LINK", placeholder="Paste link")
    elif project == "Other Tasks":
        st.markdown("<div class='form-section-title'>Other task details</div>", unsafe_allow_html=True)
        details = st.text_area("DETAILS", placeholder="Write task details", height=145)
        uploaded_files = st.file_uploader(
            "UPLOAD FILE OR IMAGE",
            type=["png", "jpg", "jpeg", "webp", "pdf", "docx", "xlsx", "csv", "txt"],
            accept_multiple_files=True,
        )

    save = st.button("+ Save task", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if save:
        errors = []
        if member == "Select member...":
            errors.append("Pick the team member name.")
        if status == "Select status...":
            errors.append("Pick the status.")
        if project == "Select project...":
            errors.append("Pick the project type.")

        if project == "Summaries":
            if not title.strip():
                errors.append("Write the summary title.")
            if not link.strip():
                errors.append("Add the link.")
            if int(word_count or 0) <= 0:
                errors.append("Add the word count.")
        elif project == "Audio":
            if not title.strip():
                errors.append("Write the audio title.")
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
            return

        insert_record(
            task_date=task_date,
            member=member,
            status=status,
            project=project,
            title=title,
            link=link,
            word_count=word_count,
            duration=duration,
            details=details,
            uploaded_files=uploaded_files,
        )
        st.session_state.selected_member = member
        st.success("Task saved successfully.")


def team_details_page(df: pd.DataFrame) -> None:
    selected = st.session_state.selected_member
    page_header("Team Details", f"Records for {selected}. Click any team member in the sidebar to switch.")

    st.markdown("<div class='filters-card'>", unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        date_filter = st.selectbox("DATE", ["This week", "Today", "Last week", "This month", "All time", "Custom range"])
    start_date = end_date = None
    with f2:
        if date_filter == "Custom range":
            start_date = st.date_input("FROM", value=date.today() - timedelta(days=7))
        else:
            selected_project = st.selectbox("PROJECT", ["All Projects"] + PROJECTS)
    with f3:
        if date_filter == "Custom range":
            end_date = st.date_input("TO", value=date.today())
        else:
            selected_status = st.selectbox("STATUS", ["All Statuses"] + STATUSES)
    with f4:
        if date_filter == "Custom range":
            selected_project = st.selectbox("PROJECT", ["All Projects"] + PROJECTS)
            selected_status = "All Statuses"
        else:
            st.write("")
    st.markdown("</div>", unsafe_allow_html=True)

    member_df = df[df["member"] == selected].copy() if not df.empty else df
    member_df = apply_date_filter(member_df, date_filter, start_date, end_date)
    if selected_project != "All Projects":
        member_df = member_df[member_df["project"] == selected_project]
    if selected_status != "All Statuses":
        member_df = member_df[member_df["status"] == selected_status]

    stat_cards(member_df)
    render_records_table(member_df, f"{selected} records", "Filtered by the selected date and project/status options.")

    if not member_df.empty:
        st.markdown("### Record actions")
        for _, row in member_df.iterrows():
            title = row.get("title") or row.get("details") or "Untitled task"
            with st.expander(f"{row['task_date']} · {row['project']} · {title}"):
                if row.get("link"):
                    st.markdown(f"**Link:** [{row['link']}]({row['link']})")
                if row.get("duration"):
                    st.write(f"**Duration:** {row['duration']}")
                if row.get("details"):
                    st.write(f"**Details:** {row['details']}")

                files = row.get("files") or []
                if files:
                    st.write("**Files**")
                    for file_info in files:
                        st.write(file_info.get("name", "file"))
                        file_path = Path(file_info.get("path", ""))
                        if file_path.exists():
                            if str(file_info.get("type", "")).startswith("image"):
                                st.image(str(file_path), width=320)
                            with open(file_path, "rb") as fh:
                                st.download_button(
                                    f"Download {file_info.get('name', 'file')}",
                                    data=fh.read(),
                                    file_name=file_info.get("name", "file"),
                                    key=f"download_{row['id']}_{file_info.get('name', 'file')}",
                                )

                with st.form(f"edit_{row['id']}"):
                    e1, e2 = st.columns(2)
                    with e1:
                        new_status = st.selectbox("Status", STATUSES, index=STATUSES.index(row["status"]) if row["status"] in STATUSES else 0)
                        new_title = st.text_input("Title", value=row.get("title") or "")
                        new_wc = st.number_input("WC", min_value=0, step=1, value=int(row.get("word_count") or 0))
                    with e2:
                        new_link = st.text_input("Link", value=row.get("link") or "")
                        new_duration = st.text_input("Duration", value=row.get("duration") or "")
                        new_details = st.text_area("Details", value=row.get("details") or "")
                    b1, b2 = st.columns(2)
                    with b1:
                        update_btn = st.form_submit_button("Save changes")
                    with b2:
                        delete_btn = st.form_submit_button("Delete record")

                if update_btn:
                    update_record(row["id"], new_status, new_title, new_link, new_wc, new_duration, new_details)
                    st.success("Record updated.")
                    st.rerun()
                if delete_btn:
                    delete_record(row["id"])
                    st.success("Record deleted.")
                    st.rerun()


def reports_page(df: pd.DataFrame) -> None:
    page_header("Reports", "Filter team performance by date, member, project and status.")

    st.markdown("<div class='filters-card'>", unsafe_allow_html=True)
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        date_filter = st.selectbox("DATE", ["This week", "Today", "Last week", "This month", "All time", "Custom range"])
    start_date = end_date = None
    with r2:
        member_filter = st.selectbox("MEMBER", ["All Members"] + TEAM_MEMBERS)
    with r3:
        project_filter = st.selectbox("PROJECT", ["All Projects"] + PROJECTS)
    with r4:
        status_filter = st.selectbox("STATUS", ["All Statuses"] + STATUSES)

    if date_filter == "Custom range":
        c1, c2 = st.columns(2)
        with c1:
            start_date = st.date_input("FROM", value=date.today() - timedelta(days=7))
        with c2:
            end_date = st.date_input("TO", value=date.today())
    st.markdown("</div>", unsafe_allow_html=True)

    report_df = apply_date_filter(df, date_filter, start_date, end_date)
    if member_filter != "All Members":
        report_df = report_df[report_df["member"] == member_filter]
    if project_filter != "All Projects":
        report_df = report_df[report_df["project"] == project_filter]
    if status_filter != "All Statuses":
        report_df = report_df[report_df["status"] == status_filter]

    stat_cards(report_df)

    if report_df.empty:
        st.markdown("<div class='empty-state'>No report data found for these filters.</div>", unsafe_allow_html=True)
        return

    grouped = (
        report_df.groupby(["member", "project"], dropna=False)
        .agg(Records=("id", "count"), Word_Count=("word_count", "sum"))
        .reset_index()
        .rename(columns={"member": "Member", "project": "Project", "Word_Count": "WC"})
    )

    st.markdown("### Summary by member and project")
    st.dataframe(grouped, hide_index=True, use_container_width=True)

    render_records_table(report_df, "Full report table", "All records matching the selected filters.")

    export_cols = ["task_date", "member", "status", "project", "title", "link", "word_count", "duration", "details"]
    st.download_button(
        "Download report CSV",
        data=report_df[export_cols].to_csv(index=False).encode("utf-8-sig"),
        file_name="rawi_team_report.csv",
        mime="text/csv",
    )


def main() -> None:
    inject_css()
    init_state()
    init_db()
    df = load_records()
    sidebar()

    if st.session_state.page == "Upload":
        upload_page()
    elif st.session_state.page == "Team Details":
        team_details_page(df)
    elif st.session_state.page == "Reports":
        reports_page(df)


if __name__ == "__main__":
    main()
