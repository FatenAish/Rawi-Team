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

STATUSES = ["Completed", "In Process", "Review", "Edit"]
STATUS_META = {
    "Completed": {"icon": "✓", "class": "green-card", "pill": "pill-green"},
    "In Process": {"icon": "⏳", "class": "blue-card", "pill": "pill-blue"},
    "Review": {"icon": "👁", "class": "purple-card", "pill": "pill-purple"},
    "Edit": {"icon": "✎", "class": "orange-card", "pill": "pill-orange"},
}

st.set_page_config(page_title=APP_TITLE, page_icon="📊", layout="wide")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --rawi-bg: #f8f9fb;
            --rawi-panel: #ffffff;
            --rawi-border: #e9edf3;
            --rawi-text: #09111f;
            --rawi-muted: #798398;
            --rawi-blue: #3b82f6;
            --rawi-purple: #8b5cf6;
            --rawi-green: #10b981;
            --rawi-orange: #f59e0b;
            --rawi-red: #ef4444;
        }
        .stApp { background: var(--rawi-bg); }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--rawi-border);
        }
        [data-testid="stSidebar"] * { font-family: Inter, Arial, sans-serif; }
        .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px; }
        h1, h2, h3 { color: var(--rawi-text); letter-spacing: -0.03em; }
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1.2rem;
        }
        .rawi-title {
            font-size: 34px;
            line-height: 1.15;
            font-weight: 800;
            margin: 0;
        }
        .rawi-subtitle {
            color: var(--rawi-muted);
            margin-top: 0.25rem;
            font-size: 15px;
        }
        .section-card {
            background: var(--rawi-panel);
            border: 1px solid var(--rawi-border);
            border-radius: 16px;
            padding: 24px 26px;
            box-shadow: 0 1px 5px rgba(15, 23, 42, 0.04);
            margin-bottom: 18px;
        }
        .metric-card {
            background: var(--rawi-panel);
            border: 1px solid var(--rawi-border);
            border-radius: 16px;
            padding: 22px 24px;
            box-shadow: 0 1px 5px rgba(15, 23, 42, 0.04);
            min-height: 126px;
        }
        .metric-row {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .metric-icon {
            width: 52px;
            height: 52px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            border-radius: 13px;
            font-weight: 800;
            font-size: 23px;
        }
        .blue-card { background: var(--rawi-blue); }
        .purple-card { background: var(--rawi-purple); }
        .green-card { background: var(--rawi-green); }
        .orange-card { background: var(--rawi-orange); }
        .red-card { background: var(--rawi-red); }
        .metric-label { color: #586174; font-size: 14px; font-weight: 600; margin-bottom: 2px; }
        .metric-value { color: #061125; font-size: 33px; line-height: 1; font-weight: 850; letter-spacing: -0.04em; }
        .metric-note { color: #8b95a7; font-size: 13px; margin-top: 8px; }
        .panel-title { font-size: 18px; font-weight: 800; color: #061125; margin-bottom: 4px; }
        .panel-subtitle { color: #687287; font-size: 14px; margin-bottom: 20px; }
        .dist-row {
            display: grid;
            grid-template-columns: 1fr 70px 54px;
            align-items: center;
            gap: 14px;
            margin: 18px 0 8px 0;
        }
        .dist-label { color: #172033; font-weight: 700; }
        .dist-percent { color: #7a8497; font-weight: 700; text-align: right; }
        .dist-count { color: #061125; font-weight: 850; text-align: right; }
        .bar-track { width: 100%; height: 8px; background: #edf0f4; border-radius: 999px; overflow: hidden; margin-top: 10px; }
        .bar-fill { height: 100%; border-radius: 999px; }
        .fill-blue { background: var(--rawi-blue); }
        .fill-purple { background: var(--rawi-purple); }
        .fill-green { background: var(--rawi-green); }
        .fill-orange { background: var(--rawi-orange); }
        .fill-red { background: var(--rawi-red); }
        .pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 800;
        }
        .pill-green { background: #dcfce7; color: #15803d; }
        .pill-blue { background: #dbeafe; color: #1d4ed8; }
        .pill-purple { background: #ede9fe; color: #6d28d9; }
        .pill-orange { background: #ffedd5; color: #c2410c; }
        .pill-gray { background: #eef2f7; color: #667085; }
        .sidebar-logo { font-size: 23px; font-weight: 900; color: #111827; padding: 0.5rem 0 1.5rem 0; }
        .sidebar-section { color: #7a8497; font-size: 13px; font-weight: 700; margin-top: 1.25rem; margin-bottom: 0.35rem; }
        .small-muted { color: #7a8497; font-size: 13px; }
        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid var(--rawi-border);
            border-radius: 16px;
            padding: 18px 20px;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 12px;
            border: 1px solid var(--rawi-border);
            font-weight: 700;
        }
        .stForm {
            background: #ffffff;
            border: 1px solid var(--rawi-border);
            border-radius: 16px;
            padding: 10px 16px 18px 16px;
        }
        hr { border-color: #edf0f4; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS performance_records (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                week_start TEXT NOT NULL,
                member TEXT NOT NULL,
                title TEXT NOT NULL,
                details TEXT,
                status TEXT NOT NULL,
                source_links TEXT,
                source_files TEXT
            )
            """
        )
        conn.commit()


def load_records() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM performance_records ORDER BY created_at DESC", conn)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "id",
                "created_at",
                "week_start",
                "member",
                "title",
                "details",
                "status",
                "source_links",
                "source_files",
            ]
        )
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["week_start"] = pd.to_datetime(df["week_start"], errors="coerce").dt.date
    df["source_links_list"] = df["source_links"].apply(lambda x: json.loads(x) if x else [])
    df["source_files_list"] = df["source_files"].apply(lambda x: json.loads(x) if x else [])
    return df


def save_uploaded_files(record_id: str, uploaded_files) -> list[dict]:
    saved = []
    folder = UPLOAD_DIR / record_id
    folder.mkdir(parents=True, exist_ok=True)

    for uploaded_file in uploaded_files or []:
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
    member: str,
    week_start: date,
    title: str,
    details: str,
    status: str,
    source_links: list[str],
    uploaded_files,
) -> str:
    record_id = str(uuid.uuid4())
    files = save_uploaded_files(record_id, uploaded_files)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO performance_records
            (id, created_at, week_start, member, title, details, status, source_links, source_files)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                datetime.now().isoformat(timespec="seconds"),
                week_start.isoformat(),
                member,
                title.strip(),
                details.strip(),
                status,
                json.dumps(source_links, ensure_ascii=False),
                json.dumps(files, ensure_ascii=False),
            ),
        )
        conn.commit()
    return record_id


def delete_record(record_id: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM performance_records WHERE id = ?", (record_id,))
        conn.commit()


def render_metric_card(label: str, value: str, note: str, icon: str, color_class: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-row">
                <div class="metric-icon {color_class}">{icon}</div>
                <div>
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                    <div class="metric-note">{note}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_distribution(df: pd.DataFrame) -> None:
    total = len(df)
    st.markdown(
        """
        <div class="section-card">
            <div class="panel-title">Performance by Status</div>
            <div class="panel-subtitle">Weekly work distribution across the team</div>
        """,
        unsafe_allow_html=True,
    )

    if total == 0:
        st.info("No records yet. Add the first weekly performance entry.")
    else:
        color_map = {
            "Completed": "fill-green",
            "In Process": "fill-blue",
            "Review": "fill-purple",
            "Edit": "fill-orange",
        }
        for status in STATUSES:
            count = int((df["status"] == status).sum())
            percent = round((count / total) * 100) if total else 0
            st.markdown(
                f"""
                <div class="dist-row">
                    <div class="dist-label">{status}</div>
                    <div class="dist-percent">{percent}%</div>
                    <div class="dist-count">{count}</div>
                </div>
                <div class="bar-track"><div class="bar-fill {color_map[status]}" style="width:{percent}%;"></div></div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def render_weekly_table(df: pd.DataFrame) -> None:
    st.markdown(
        """
        <div class="section-card">
            <div class="panel-title">Weekly Trends</div>
            <div class="panel-subtitle">Performance added over the last 8 weeks</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("No weekly trends yet.")
        return

    today_week = get_week_start(date.today())
    weeks = [today_week - timedelta(weeks=i) for i in range(7, -1, -1)]
    rows = []
    for week in weeks:
        week_df = df[df["week_start"] == week]
        row = {"Week": week.strftime("%d %b %Y")}
        for status in STATUSES:
            row[status] = int((week_df["status"] == status).sum())
        row["Total"] = len(week_df)
        rows.append(row)

    trend_df = pd.DataFrame(rows)
    st.dataframe(trend_df, hide_index=True, use_container_width=True)


def render_team_table(df: pd.DataFrame, selected_week: date) -> None:
    week_df = df[df["week_start"] == selected_week]
    rows = []
    for member in TEAM_MEMBERS:
        member_df = week_df[week_df["member"] == member]
        total = len(member_df)
        completed = int((member_df["status"] == "Completed").sum())
        completion_rate = f"{round((completed / total) * 100)}%" if total else "0%"
        rows.append(
            {
                "Team Member": member,
                "Completed": completed,
                "In Process": int((member_df["status"] == "In Process").sum()),
                "Review": int((member_df["status"] == "Review").sum()),
                "Edit": int((member_df["status"] == "Edit").sum()),
                "Total": total,
                "Completion Rate": completion_rate,
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def sidebar_nav() -> str:
    st.sidebar.markdown('<div class="sidebar-logo">Rawi</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sidebar-section">Main</div>', unsafe_allow_html=True)
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Upload Performance", "Team Records", "Reports"],
        label_visibility="collapsed",
    )
    st.sidebar.markdown('<div class="sidebar-section">Team</div>', unsafe_allow_html=True)
    st.sidebar.caption("Faten Aish")
    st.sidebar.caption("Yazan Dmara")
    st.sidebar.caption("Kamal Arslan")
    st.sidebar.caption("Nour Aldeen")
    st.sidebar.caption("Doha Alrefai")
    st.sidebar.caption("Ali")
    return page


def dashboard_page(df: pd.DataFrame) -> None:
    st.markdown(
        """
        <div class="topbar">
            <div>
                <h1 class="rawi-title">Rawi Team KPI Dashboard</h1>
                <div class="rawi-subtitle">Weekly performance tracking for content, audio, review and editing work.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_week = get_week_start(date.today())
    week_df = df[df["week_start"] == current_week] if not df.empty else df
    completed = int((week_df["status"] == "Completed").sum()) if not week_df.empty else 0
    in_process = int((week_df["status"] == "In Process").sum()) if not week_df.empty else 0
    review = int((week_df["status"] == "Review").sum()) if not week_df.empty else 0
    edit = int((week_df["status"] == "Edit").sum()) if not week_df.empty else 0
    total_files = sum(len(x) for x in df.get("source_files_list", pd.Series(dtype=object))) if not df.empty else 0
    total_links = sum(len(x) for x in df.get("source_links_list", pd.Series(dtype=object))) if not df.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Team Members", str(len(TEAM_MEMBERS)), "Rawi performance users", "👥", "blue-card")
    with c2:
        render_metric_card("Completed", str(completed), "this week", "✓", "green-card")
    with c3:
        render_metric_card("In Process", str(in_process), "this week", "⏳", "purple-card")
    with c4:
        render_metric_card("Review / Edit", str(review + edit), "this week", "✎", "orange-card")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        render_metric_card("Total Records", str(len(df)), "all submitted tasks", "▣", "blue-card")
    with c6:
        render_metric_card("Source Links", str(total_links), "attached references", "🔗", "purple-card")
    with c7:
        render_metric_card("Uploaded Files", str(total_files), "images or documents", "↥", "green-card")
    with c8:
        rate = f"{round((completed / len(week_df)) * 100)}%" if len(week_df) else "0%"
        render_metric_card("Completion Rate", rate, "current week", "%", "orange-card")

    left, right = st.columns([1, 1])
    with left:
        render_status_distribution(week_df)
    with right:
        render_weekly_table(df)

    st.markdown(
        f"""
        <div class="section-card">
            <div class="panel-title">Team Performance</div>
            <div class="panel-subtitle">Current week starts on {current_week.strftime('%d %b %Y')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_team_table(df, current_week)


def upload_page() -> None:
    st.markdown("<h1 class='rawi-title'>Upload Weekly Performance</h1>", unsafe_allow_html=True)
    st.caption("Team members can add their weekly work, status, source links and proof files.")

    with st.form("performance_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            member = st.selectbox("Team Member", TEAM_MEMBERS)
        with col2:
            week_start = st.date_input("Week Start", value=get_week_start(date.today()))
        with col3:
            status = st.selectbox("Status", STATUSES)

        title = st.text_input("Performance Item / Task Title", placeholder="Example: Finished 8 book reviews")
        details = st.text_area(
            "Details",
            placeholder="Write the work done, blockers, notes, or what needs review.",
            height=140,
        )
        source_links_text = st.text_area(
            "Source Links",
            placeholder="Add one link per line: Airtable, Google Drive, published URL, etc.",
            height=90,
        )
        uploaded_files = st.file_uploader(
            "Upload Source Files or Images",
            type=["png", "jpg", "jpeg", "webp", "pdf", "docx", "xlsx", "csv", "txt"],
            accept_multiple_files=True,
        )
        submitted = st.form_submit_button("Save Performance")

    if submitted:
        if not title.strip():
            st.error("Please add a task title before saving.")
            return
        source_links = [line.strip() for line in source_links_text.splitlines() if line.strip()]
        record_id = insert_record(member, week_start, title, details, status, source_links, uploaded_files)
        st.success(f"Performance saved successfully. Record ID: {record_id[:8]}")


def records_page(df: pd.DataFrame) -> None:
    st.markdown("<h1 class='rawi-title'>Team Records</h1>", unsafe_allow_html=True)
    st.caption("Filter, review, export or delete submitted performance records.")

    if df.empty:
        st.info("No records yet.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        member_filter = st.multiselect("Team Member", TEAM_MEMBERS, default=TEAM_MEMBERS)
    with col2:
        status_filter = st.multiselect("Status", STATUSES, default=STATUSES)
    with col3:
        selected_week = st.date_input("Week", value=get_week_start(date.today()))

    filtered = df[
        (df["member"].isin(member_filter))
        & (df["status"].isin(status_filter))
        & (df["week_start"] == selected_week)
    ].copy()

    export_cols = ["created_at", "week_start", "member", "title", "details", "status", "source_links"]
    st.download_button(
        "Download Filtered Records CSV",
        data=filtered[export_cols].to_csv(index=False).encode("utf-8-sig"),
        file_name=f"rawi_performance_{selected_week.isoformat()}.csv",
        mime="text/csv",
    )

    if filtered.empty:
        st.warning("No matching records for the selected filters.")
        return

    table_df = filtered[["created_at", "week_start", "member", "title", "status"]].copy()
    table_df["created_at"] = table_df["created_at"].dt.strftime("%d %b %Y %H:%M")
    st.dataframe(table_df, hide_index=True, use_container_width=True)

    st.markdown("---")
    for _, row in filtered.iterrows():
        status_class = STATUS_META[row["status"]]["pill"]
        with st.expander(f"{row['member']} · {row['title']} · {row['status']}"):
            st.markdown(f"<span class='pill {status_class}'>{row['status']}</span>", unsafe_allow_html=True)
            st.write(row.get("details") or "No details added.")

            links = row.get("source_links_list", [])
            if links:
                st.markdown("**Source Links**")
                for link in links:
                    st.markdown(f"- [{link}]({link})")

            files = row.get("source_files_list", [])
            if files:
                st.markdown("**Uploaded Files**")
                for file_info in files:
                    file_path = Path(file_info.get("path", ""))
                    st.write(f"{file_info.get('name')} · {round((file_info.get('size', 0) or 0) / 1024, 1)} KB")
                    if file_path.exists():
                        if str(file_info.get("type", "")).startswith("image"):
                            st.image(str(file_path), width=320)
                        with open(file_path, "rb") as f:
                            st.download_button(
                                f"Download {file_info.get('name')}",
                                data=f.read(),
                                file_name=file_info.get("name"),
                                key=f"download_{row['id']}_{file_info.get('name')}",
                            )

            delete_col, _ = st.columns([1, 5])
            with delete_col:
                if st.button("Delete", key=f"delete_{row['id']}"):
                    delete_record(row["id"])
                    st.success("Record deleted. Refreshing...")
                    st.rerun()


def reports_page(df: pd.DataFrame) -> None:
    st.markdown("<h1 class='rawi-title'>Reports</h1>", unsafe_allow_html=True)
    st.caption("Simple reporting for weekly follow-up meetings.")

    if df.empty:
        st.info("No records yet.")
        return

    col1, col2 = st.columns(2)
    with col1:
        selected_week = st.date_input("Report Week", value=get_week_start(date.today()))
    with col2:
        selected_member = st.selectbox("Member", ["All Team"] + TEAM_MEMBERS)

    report_df = df[df["week_start"] == selected_week]
    if selected_member != "All Team":
        report_df = report_df[report_df["member"] == selected_member]

    st.markdown(
        f"""
        <div class="section-card">
            <div class="panel-title">Weekly Summary</div>
            <div class="panel-subtitle">Week of {selected_week.strftime('%d %b %Y')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", len(report_df))
    c2.metric("Completed", int((report_df["status"] == "Completed").sum()))
    c3.metric("Review", int((report_df["status"] == "Review").sum()))
    c4.metric("Edit", int((report_df["status"] == "Edit").sum()))

    if report_df.empty:
        st.warning("No data for this report filter.")
        return

    grouped = report_df.groupby(["member", "status"]).size().reset_index(name="Count")
    st.dataframe(grouped, hide_index=True, use_container_width=True)

    st.markdown("### Notes by Member")
    for member in sorted(report_df["member"].unique()):
        member_df = report_df[report_df["member"] == member]
        st.markdown(f"**{member}**")
        for _, row in member_df.iterrows():
            st.write(f"- {row['status']}: {row['title']}")


def main() -> None:
    inject_css()
    init_db()
    page = sidebar_nav()
    df = load_records()

    if page == "Dashboard":
        dashboard_page(df)
    elif page == "Upload Performance":
        upload_page()
    elif page == "Team Records":
        records_page(df)
    elif page == "Reports":
        reports_page(df)


if __name__ == "__main__":
    main()
