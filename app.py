
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

STATUSES = ["Completed", "In Process", "Upload", "Review"]
PROJECTS = ["Summaries", "Audio", "Other tasks"]

STATUS_COLORS = {
    "Completed": "#10b981",
    "In Process": "#3b82f6",
    "Upload": "#f59e0b",
    "Review": "#8b5cf6",
}

PROJECT_COLORS = {
    "Summaries": "#e0f2fe",
    "Audio": "#ede9fe",
    "Other tasks": "#fef3c7",
}

st.set_page_config(page_title=APP_TITLE, page_icon="✅", layout="wide")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f7f9fc;
            --panel: #ffffff;
            --border: #d9dee8;
            --border-soft: #edf0f5;
            --text: #111827;
            --muted: #667085;
            --green: #10b981;
            --blue: #3b82f6;
            --purple: #8b5cf6;
            --orange: #f59e0b;
            --cyan: #12cfd0;
        }

        .stApp {
            background: var(--bg);
        }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 100%;
        }

        h1, h2, h3, p, div, span, label {
            font-family: Inter, Arial, sans-serif;
        }

        h1 {
            color: var(--text);
            letter-spacing: -0.04em;
        }

        div[data-testid="stSidebar"] {
            display: none;
        }

        .rawi-shell {
            border: 1px solid var(--border);
            border-radius: 18px;
            overflow: hidden;
            background: #fff;
            box-shadow: 0 1px 5px rgba(15, 23, 42, 0.04);
        }

        .rawi-topbar {
            height: 68px;
            border-bottom: 1px solid var(--border);
            background: #fff;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 22px;
        }

        .rawi-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 22px;
            font-weight: 850;
            color: #0f172a;
        }

        .rawi-logo {
            width: 42px;
            height: 42px;
            border-radius: 10px;
            background: #13cfd0;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: #0f172a;
            font-weight: 900;
        }

        .rawi-tabs {
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .rawi-chip {
            padding: 7px 12px;
            border-radius: 999px;
            border: 1px solid var(--border);
            background: #fff;
            color: var(--muted);
            font-size: 13px;
            font-weight: 700;
        }

        .page-title {
            font-size: 27px;
            font-weight: 850;
            color: #101828;
            letter-spacing: -0.04em;
            margin: 0 0 4px 0;
        }

        .page-subtitle {
            color: #667085;
            font-size: 14px;
            margin-bottom: 18px;
        }

        .section-card {
            background: #fff;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.03);
        }

        .form-card {
            background: #fff;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 22px;
            margin-top: 8px;
        }

        .member-panel {
            background: #fff;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 14px;
            min-height: 640px;
        }

        .member-title {
            color: #667085;
            font-size: 13px;
            font-weight: 800;
            padding: 8px 8px 12px 8px;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }

        .member-active {
            background: #f0fdfa;
            border-left: 4px solid #14b8a6;
            border-radius: 10px;
            padding: 11px 12px;
            font-weight: 850;
            color: #0f172a;
            margin-bottom: 8px;
        }

        .table-card {
            background: #fff;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 0;
            overflow: hidden;
        }

        .table-header {
            background: #e9fbfb;
            border-bottom: 1px solid var(--border);
            padding: 14px 18px;
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: center;
        }

        .table-title {
            font-weight: 850;
            color: #0f172a;
            font-size: 16px;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }

        .metric-box {
            background: #fff;
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px;
        }

        .metric-label {
            color: #667085;
            font-size: 12px;
            font-weight: 750;
        }

        .metric-value {
            color: #101828;
            font-size: 27px;
            font-weight: 900;
            letter-spacing: -0.04em;
            margin-top: 3px;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 850;
            color: #fff;
        }

        .small-muted {
            color: #667085;
            font-size: 13px;
        }

        div[data-testid="stButton"] > button {
            width: 100%;
            justify-content: flex-start;
            border-radius: 10px;
            border: 1px solid transparent;
            background: transparent;
            font-weight: 750;
            color: #101828;
            padding: 0.55rem 0.7rem;
        }

        div[data-testid="stButton"] > button:hover {
            background: #f2f4f7;
            border-color: #e5e7eb;
        }

        .stButton > button[kind="primary"] {
            background: #14b8a6 !important;
            color: white !important;
            border-color: #14b8a6 !important;
            justify-content: center !important;
        }

        .stDownloadButton > button {
            border-radius: 10px;
            font-weight: 750;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 0 !important;
        }

        .record-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 8px 0 12px 0;
        }

        .meta-chip {
            background: #f2f4f7;
            color: #475467;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 750;
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


def topbar() -> None:
    st.markdown(
        """
        <div class="rawi-shell">
            <div class="rawi-topbar">
                <div class="rawi-brand">
                    <span class="rawi-logo">R</span>
                    <span>Rawi Team Performance</span>
                </div>
                <div class="rawi-tabs">
                    <span class="rawi-chip">Team Details</span>
                    <span class="rawi-chip">Upload</span>
                    <span class="rawi-chip">Reports</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")


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

        existing = {
            row[1] for row in conn.execute("PRAGMA table_info(performance_records)").fetchall()
        }
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

    if df.empty:
        return pd.DataFrame(columns=expected_cols + ["source_files_list"])

    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")

    # Backward compatibility for older rows that had week_start/title/source_links.
    if "week_start" in df.columns:
        df["task_date"] = df["task_date"].fillna(df["week_start"])
    if "title" in df.columns:
        df["summary_name"] = df["summary_name"].fillna(df["title"])
    if "source_links" in df.columns:
        def first_link(value):
            links = safe_json_loads(value)
            return links[0] if links else None
        df["link"] = df["link"].fillna(df["source_links"].apply(first_link))

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
                json.dumps(files, ensure_ascii=False),
            ),
        )
        conn.commit()

    return record_id


def delete_record(record_id: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM performance_records WHERE id = ?", (record_id,))
        conn.commit()


def update_record(
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


def date_range_from_filter(filter_name: str, start_date=None, end_date=None):
    today = date.today()
    if filter_name == "Today":
        return today, today
    if filter_name == "This week":
        week_start = today - timedelta(days=today.weekday())
        return week_start, week_start + timedelta(days=6)
    if filter_name == "Last week":
        this_week = today - timedelta(days=today.weekday())
        last_week = this_week - timedelta(days=7)
        return last_week, last_week + timedelta(days=6)
    if filter_name == "This month":
        month_start = today.replace(day=1)
        return month_start, today
    if filter_name == "Custom range":
        return start_date, end_date
    return None, None


def filter_by_date(df: pd.DataFrame, filter_name: str, start_date=None, end_date=None):
    if df.empty:
        return df

    start, end = date_range_from_filter(filter_name, start_date, end_date)
    if start is None or end is None:
        return df

    return df[(df["task_date"] >= start) & (df["task_date"] <= end)]


def page_selector() -> None:
    cols = st.columns([1.2, 1.1, 5])
    with cols[0]:
        if st.button("Team Details", use_container_width=True):
            st.session_state.page = "Team Details"
    with cols[1]:
        if st.button("Upload", use_container_width=True):
            st.session_state.page = "Upload"
    with cols[2]:
        if st.button("Reports", use_container_width=False):
            st.session_state.page = "Reports"


def render_member_buttons() -> None:
    st.markdown("<div class='member-title'>Team members</div>", unsafe_allow_html=True)
    for member in TEAM_MEMBERS:
        if member == st.session_state.selected_member:
            st.markdown(f"<div class='member-active'>{member}</div>", unsafe_allow_html=True)
        else:
            if st.button(member, key=f"member_{member}", use_container_width=True):
                st.session_state.selected_member = member
                st.rerun()


def format_file_count(files: list[dict]) -> str:
    if not files:
        return ""
    return f"{len(files)} file" if len(files) == 1 else f"{len(files)} files"


def build_table_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=["Date", "Status", "Project", "Summary Name / Details", "URL", "WC", "Duration", "Files", "Updated"]
        )

    table = df.copy()
    table["Date"] = table["task_date"].apply(lambda x: x.strftime("%B %d, %Y") if pd.notna(x) else "")
    table["Status"] = table["status"].fillna("")
    table["Project"] = table["project"].fillna("")
    table["Summary Name / Details"] = table.apply(
        lambda r: r["summary_name"] if str(r.get("summary_name") or "").strip() else str(r.get("details") or "")[:80],
        axis=1,
    )
    table["URL"] = table["link"].fillna("")
    table["WC"] = table["word_count"].replace(0, "")
    table["Duration"] = table["duration"].fillna("")
    table["Files"] = table["source_files_list"].apply(format_file_count)
    table["Updated"] = table["updated_at"].apply(
        lambda x: x.strftime("%b %d, %H:%M") if pd.notna(x) else ""
    )
    return table[["Date", "Status", "Project", "Summary Name / Details", "URL", "WC", "Duration", "Files", "Updated"]]


def team_details_page(df: pd.DataFrame) -> None:
    st.markdown("<div class='page-title'>Team Details</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='page-subtitle'>Press a team member name to open their records. Use the date filter to review the needed period.</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.05, 4.6], gap="medium")

    with left:
        st.markdown("<div class='member-panel'>", unsafe_allow_html=True)
        render_member_buttons()
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        selected_member = st.session_state.selected_member
        member_df = df[df["member"] == selected_member].copy() if not df.empty else df

        f1, f2, f3, f4 = st.columns([1.1, 1, 1, 1])
        with f1:
            time_filter = st.selectbox(
                "Date filter",
                ["This week", "Today", "Last week", "This month", "All time", "Custom range"],
                index=0,
            )
        start_date = end_date = None
        if time_filter == "Custom range":
            with f2:
                start_date = st.date_input("From", value=date.today() - timedelta(days=7))
            with f3:
                end_date = st.date_input("To", value=date.today())
        else:
            with f2:
                status_filter = st.multiselect("Status", STATUSES, default=STATUSES)
            with f3:
                project_filter = st.multiselect("Project", PROJECTS, default=PROJECTS)

        if time_filter == "Custom range":
            with f4:
                status_filter = st.multiselect("Status", STATUSES, default=STATUSES)
            project_filter = PROJECTS

        filtered = filter_by_date(member_df, time_filter, start_date, end_date)
        filtered = filtered[
            filtered["status"].isin(status_filter) & filtered["project"].isin(project_filter)
        ].copy() if not filtered.empty else filtered

        total_wc = int(filtered["word_count"].sum()) if not filtered.empty else 0
        total_files = sum(len(x) for x in filtered["source_files_list"]) if not filtered.empty else 0

        st.markdown(
            f"""
            <div class="metric-grid">
                <div class="metric-box"><div class="metric-label">Selected Member</div><div class="metric-value" style="font-size:21px;">{selected_member}</div></div>
                <div class="metric-box"><div class="metric-label">Records</div><div class="metric-value">{len(filtered)}</div></div>
                <div class="metric-box"><div class="metric-label">Completed</div><div class="metric-value">{int((filtered["status"] == "Completed").sum()) if not filtered.empty else 0}</div></div>
                <div class="metric-box"><div class="metric-label">Total WC</div><div class="metric-value">{total_wc:,}</div></div>
                <div class="metric-box"><div class="metric-label">Files</div><div class="metric-value">{total_files}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="table-card">
                <div class="table-header">
                    <div class="table-title">{selected_member} Records</div>
                    <div class="small-muted">Table opens after selecting a member name</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if filtered.empty:
            st.info("No records found for this member and date filter.")
        else:
            table_df = build_table_df(filtered)

            st.dataframe(
                table_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "URL": st.column_config.LinkColumn("URL", display_text="Open link"),
                    "WC": st.column_config.NumberColumn("WC", format="%d"),
                },
            )

            export_df = filtered[
                ["task_date", "member", "status", "project", "summary_name", "link", "word_count", "duration", "details"]
            ].copy()
            st.download_button(
                "Download selected member records CSV",
                data=export_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"{selected_member.replace(' ', '_')}_records.csv",
                mime="text/csv",
            )

            st.markdown("### Open record details")
            for _, row in filtered.iterrows():
                label_title = row["summary_name"] or row["details"] or "Untitled record"
                with st.expander(f"{row['task_date']} · {row['project']} · {label_title}"):
                    status_color = STATUS_COLORS.get(row["status"], "#667085")
                    st.markdown(
                        f"""
                        <div class="record-meta">
                            <span class="status-pill" style="background:{status_color};">{row["status"]}</span>
                            <span class="meta-chip">{row["project"]}</span>
                            <span class="meta-chip">{row["task_date"]}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if row["summary_name"]:
                        st.write(f"**Summary Name:** {row['summary_name']}")
                    if row["link"]:
                        st.markdown(f"**Link:** [{row['link']}]({row['link']})")
                    if row["word_count"]:
                        st.write(f"**WC:** {int(row['word_count']):,}")
                    if row["duration"]:
                        st.write(f"**Duration:** {row['duration']}")
                    if row["details"]:
                        st.write(f"**Details:** {row['details']}")

                    files = row.get("source_files_list", [])
                    if files:
                        st.write("**Files**")
                        for file_info in files:
                            path = Path(file_info.get("path", ""))
                            st.write(f"{file_info.get('name')} · {round((file_info.get('size', 0) or 0) / 1024, 1)} KB")
                            if path.exists():
                                if str(file_info.get("type", "")).startswith("image"):
                                    st.image(str(path), width=350)
                                with open(path, "rb") as handle:
                                    st.download_button(
                                        f"Download {file_info.get('name')}",
                                        data=handle.read(),
                                        file_name=file_info.get("name"),
                                        key=f"download_{row['id']}_{file_info.get('name')}",
                                    )

                    with st.form(f"edit_form_{row['id']}"):
                        st.write("Edit record")
                        e1, e2 = st.columns(2)
                        with e1:
                            new_status = st.selectbox(
                                "Status",
                                STATUSES,
                                index=STATUSES.index(row["status"]) if row["status"] in STATUSES else 0,
                                key=f"edit_status_{row['id']}",
                            )
                            new_summary_name = st.text_input(
                                "Summary Name / Title",
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
                        with e2:
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

                        save_col, delete_col = st.columns([1, 1])
                        with save_col:
                            save_edit = st.form_submit_button("Save changes")
                        with delete_col:
                            delete_it = st.form_submit_button("Delete record")

                    if save_edit:
                        update_record(row["id"], new_status, new_summary_name, new_link, new_wc, new_duration, new_details)
                        st.success("Record updated.")
                        st.rerun()

                    if delete_it:
                        delete_record(row["id"])
                        st.success("Record deleted.")
                        st.rerun()


def upload_page() -> None:
    st.markdown("<div class='page-title'>Upload Performance</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='page-subtitle'>Choose the team member, status and project. The fields change based on the selected project.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='form-card'>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        member = st.selectbox("Team member", ["Select member..."] + TEAM_MEMBERS)
    with c2:
        task_date = st.date_input("Date", value=date.today())

    c3, c4 = st.columns(2)
    with c3:
        status = st.selectbox("Status", ["Select status..."] + STATUSES)
    with c4:
        project = st.selectbox("Project", ["Select project..."] + PROJECTS)

    summary_name = ""
    link = ""
    word_count = 0
    duration = ""
    details = ""
    uploaded_files = None

    if project == "Summaries":
        st.markdown("### Summary details")
        s1, s2 = st.columns([2, 1])
        with s1:
            summary_name = st.text_input("Summary name", placeholder="Example: The Secret Garden summary")
        with s2:
            word_count = st.number_input("WC", min_value=0, step=1, value=0)
        link = st.text_input("Link", placeholder="Paste the summary/source link")

    elif project == "Audio":
        st.markdown("### Audio details")
        a1, a2 = st.columns([2, 1])
        with a1:
            summary_name = st.text_input("Summary name", placeholder="Example: The Secret Garden audio")
        with a2:
            duration = st.text_input("Duration", placeholder="Example: 12 min or 00:12:30")
        link = st.text_input("Link", placeholder="Paste the audio/source link")

    elif project == "Other tasks":
        st.markdown("### Other task details")
        details = st.text_area("Details", placeholder="Write what was done, what needs review, or any notes.", height=150)
        uploaded_files = st.file_uploader(
            "Upload file or image",
            type=["png", "jpg", "jpeg", "webp", "pdf", "docx", "xlsx", "csv", "txt"],
            accept_multiple_files=True,
        )

    submit = st.button("+ Add task", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if submit:
        errors = []
        if member == "Select member...":
            errors.append("Pick the team member name.")
        if status == "Select status...":
            errors.append("Pick the status.")
        if project == "Select project...":
            errors.append("Pick the project.")

        if project == "Summaries":
            if not summary_name.strip():
                errors.append("Write the summary name.")
            if not link.strip():
                errors.append("Add the link.")
            if not word_count:
                errors.append("Add the WC.")
        elif project == "Audio":
            if not summary_name.strip():
                errors.append("Write the summary name.")
            if not link.strip():
                errors.append("Add the link.")
            if not duration.strip():
                errors.append("Add the duration.")
        elif project == "Other tasks":
            has_files = bool(uploaded_files)
            if not details.strip() and not has_files:
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
            summary_name=summary_name,
            link=link,
            word_count=word_count,
            duration=duration,
            details=details,
            uploaded_files=uploaded_files,
        )
        st.success("Task added successfully.")
        st.session_state.selected_member = member


def reports_page(df: pd.DataFrame) -> None:
    st.markdown("<div class='page-title'>Reports</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Filter reports by date, member, status and project.</div>", unsafe_allow_html=True)

    if df.empty:
        st.info("No records yet.")
        return

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        time_filter = st.selectbox(
            "Date filter",
            ["This week", "Today", "Last week", "This month", "All time", "Custom range"],
            index=0,
        )
    start_date = end_date = None
    if time_filter == "Custom range":
        with r2:
            start_date = st.date_input("From", value=date.today() - timedelta(days=7))
        with r3:
            end_date = st.date_input("To", value=date.today())
        with r4:
            selected_member = st.selectbox("Member", ["All Team"] + TEAM_MEMBERS)
    else:
        with r2:
            selected_member = st.selectbox("Member", ["All Team"] + TEAM_MEMBERS)
        with r3:
            selected_project = st.selectbox("Project", ["All Projects"] + PROJECTS)
        with r4:
            selected_status = st.selectbox("Status", ["All Statuses"] + STATUSES)

    report_df = filter_by_date(df, time_filter, start_date, end_date)

    if time_filter == "Custom range":
        selected_project = "All Projects"
        selected_status = "All Statuses"

    if selected_member != "All Team":
        report_df = report_df[report_df["member"] == selected_member]
    if selected_project != "All Projects":
        report_df = report_df[report_df["project"] == selected_project]
    if selected_status != "All Statuses":
        report_df = report_df[report_df["status"] == selected_status]

    total_wc = int(report_df["word_count"].sum()) if not report_df.empty else 0
    total_files = sum(len(x) for x in report_df["source_files_list"]) if not report_df.empty else 0

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-box"><div class="metric-label">Records</div><div class="metric-value">{len(report_df)}</div></div>
            <div class="metric-box"><div class="metric-label">Completed</div><div class="metric-value">{int((report_df["status"] == "Completed").sum()) if not report_df.empty else 0}</div></div>
            <div class="metric-box"><div class="metric-label">Summaries</div><div class="metric-value">{int((report_df["project"] == "Summaries").sum()) if not report_df.empty else 0}</div></div>
            <div class="metric-box"><div class="metric-label">Total WC</div><div class="metric-value">{total_wc:,}</div></div>
            <div class="metric-box"><div class="metric-label">Files</div><div class="metric-value">{total_files}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if report_df.empty:
        st.warning("No data for these filters.")
        return

    st.markdown("### By member and project")
    grouped = (
        report_df.groupby(["member", "project", "status"], dropna=False)
        .agg(Records=("id", "count"), WC=("word_count", "sum"))
        .reset_index()
    )
    st.dataframe(grouped, hide_index=True, use_container_width=True)

    st.markdown("### Full report table")
    st.dataframe(
        build_table_df(report_df),
        hide_index=True,
        use_container_width=True,
        column_config={"URL": st.column_config.LinkColumn("URL", display_text="Open link")},
    )

    st.download_button(
        "Download report CSV",
        data=report_df[
            ["task_date", "member", "status", "project", "summary_name", "link", "word_count", "duration", "details"]
        ].to_csv(index=False).encode("utf-8-sig"),
        file_name="rawi_report.csv",
        mime="text/csv",
    )


def main() -> None:
    inject_css()
    init_state()
    init_db()
    df = load_records()

    topbar()
    page_selector()
    st.write("")

    if st.session_state.page == "Team Details":
        team_details_page(df)
    elif st.session_state.page == "Upload":
        upload_page()
    elif st.session_state.page == "Reports":
        reports_page(df)


if __name__ == "__main__":
    main()
