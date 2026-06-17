import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Initialize session state for mock database if it doesn't exist
if 'tasks_db' not in st.session_state:
    # Pre-populating with data matching your screenshots to maintain state consistency
    st.session_state.tasks_db = pd.DataFrame([
        {
            "Date": "2026-06-17",
            "Member": "Faten Aish",
            "Project": "Summaries",
            "Details": "مقدمة: الزَّوَاجُ فِي بَيْتِ النُّبُوَّةِ",
            "Status": "Completed",
            "WC": 700,
            "Duration": None
        },
        {
            "Date": "2026-06-17",
            "Member": "Yazan Dmara",
            "Project": "Audio",
            "Details": "مقدمة: الزَّوَاجُ فِي بَيْتِ النُّبُوَّةِ",
            "Status": "Completed",
            "WC": None,
            "Duration": "00:07:00"
        },
        {
            "Date": "2026-06-17",
            "Member": "Kamal Arslan",
            "Project": "Meeting",
            "Details": "Faten",
            "Status": "Completed",
            "WC": None,
            "Duration": None
        }
    ])

def parse_duration_to_minutes(duration_str):
    """Safely converts hh:mm:ss or mm:ss strings into integer/float minutes."""
    if pd.isna(duration_str) or not duration_str or str(duration_str).strip().lower() == 'none':
        return 0
    try:
        parts = list(map(int, str(duration_str).split(':')))
        if len(parts) == 3:  # hh:mm:ss
            return parts[0] * 60 + parts[1] + parts[2] / 60
        elif len(parts) == 2:  # mm:ss
            return parts[0] + parts[1] / 60
    except Exception:
        return 0
    return 0

def generate_excel_report(report_df):
    """Generates an Excel file safely using openpyxl engine."""
    output = io.BytesIO()
    # Wrapping with openpyxl engine as requested by your export architecture
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        report_df.to_excel(writer, index=False, sheet_name='Performance Report')
    return output.getvalue()

def upload_task_page():
    st.title("Upload task")
    st.caption("Record a new task for a team member")
    
    # Form Layout
    col1, col2 = st.columns(2)
    with col1:
        member = st.selectbox("TEAM MEMBER", ["Faten Aish", "Yazan Dmara", "Kamal Arslan", "Nour Aldeen", "Doha Alrefai", "Ali"])
        status = st.selectbox("STATUS", ["Select status...", "Uploaded", "Completed", "In Progress"], index=0)
    with col2:
        date_val = st.date_input("DATE", datetime(2026, 6, 17))
        project = st.selectbox("PROJECT", ["Select project...", "Summaries", "Audio", "Meeting", "Other Tasks"], index=0)
        
    st.markdown("---")
    
    # Context-Driven Dynamic Task Fields (Resolves cross-contamination of parameters)
    details = ""
    wc_value = None
    duration_value = None
    
    if project == "Select project...":
        st.info("Select a project type above. The relevant task fields will appear here.")
        submit_disabled = True
    else:
        submit_disabled = False
        details = st.text_area("Task Details / Content Context", placeholder="e.g., Enter titles, topics or links here...")
        
        if project == "Summaries":
            st.markdown("### 📝 Summaries Configuration")
            wc_value = st.number_input("Word Count (WC)", min_value=0, step=1, value=0)
            # Explicitly force duration tracking off for summaries
            duration_value = None 
            
        elif project == "Audio":
            st.markdown("### 🎧 Audio Configuration")
            duration_input = st.text_input("Duration (Format: hh:mm:ss or mm:ss)", value="00:00:00")
            duration_value = duration_input if duration_input != "00:00:00" else None
            # Explicitly force word counts off for raw audio streams
            wc_value = None
            
        else:
            st.markdown("### ⚙️ General Task Parameters")
            # Clear metric parameters for organizational meetings/administrative items
            wc_value = None
            duration_value = None

    # Submission Action Block
    st.markdown("##")
    if st.button("✨ Save task", disabled=submit_disabled):
        if status == "Select status...":
            st.error("Please pick a valid functional context pipeline status value.")
        else:
            new_row = {
                "Date": date_val.strftime("%Y-%m-%d"),
                "Member": member,
                "Project": project,
                "Details": details,
                "Status": status,
                "WC": wc_value,
                "Duration": duration_value
            }
            # Append dynamic entry to structured persistent application memory framework
            st.session_state.tasks_db = pd.concat([st.session_state.tasks_db, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Task successfully processed and committed under reference scope '{project}' for {member}!")

def team_details_page():
    st.title("Team details")
    
    selected_member = st.sidebar.selectbox("Select Team Member Target View", ["Faten Aish", "Yazan Dmara", "Kamal Arslan", "Nour Aldeen", "Doha Alrefai", "Ali"])
    st.caption(f"Performance records for **{selected_member}**")
    
    # Filter base operational matrix
    member_df = st.session_state.tasks_db[st.session_state.tasks_db['Member'] == selected_member].copy()
    
    # Isolated Metrics Context Computing Card Calculations 
    total_records = len(member_df)
    completed_records = len(member_df[member_df['Status'] == 'Completed'])
    summaries_count = len(member_df[member_df['Project'] == 'Summaries'])
    
    # Strictly parse individual columns without carrying validation states between loops
    total_words = int(pd.to_numeric(member_df['WC'], errors='coerce').fillna(0).sum())
    
    # Render operational dashboard cards
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    m_col1.metric("RECORDS", total_records)
    m_col2.metric("COMPLETED", completed_records)
    m_col3.metric("SUMMARIES", summaries_count)
    m_col4.metric("TOTAL WORDS", f"{total_words:,}")
    m_col5.metric("FILES", 0) # Mock metric matching legacy app frame assets
    
    st.markdown("##")
    
    if total_records > 0:
        # Pre-process viewing layer column formats cleanly 
        display_df = member_df.copy()
        display_df['WC'] = display_df['WC'].apply(lambda x: f"{int(x)}" if pd.notna(x) and x is not None else "None")
        display_df['Duration'] = display_df['Duration'].fillna("None")
        
        st.dataframe(display_df[["Date", "Project", "Details", "Status", "WC", "Duration"]], use_container_width=True)
    else:
        st.info("No localized task ledger sequences recorded under this asset structure path.")

def reports_page():
    st.title("Performance Reports")
    st.caption("Filter and view overall team metrics")
    
    df = st.session_state.tasks_db.copy()
    
    # Filter Controller Bars
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        st.selectbox("DATE FILTER", ["All Time"])
    with f_col2:
        member_filter = st.selectbox("MEMBER", ["All Members"] + list(df['Member'].unique()))
    with f_col3:
        project_filter = st.selectbox("PROJECT", ["All Projects"] + list(df['Project'].unique()))
    with f_col4:
        status_filter = st.selectbox("STATUS", ["All Statuses"] + list(df['Status'].unique()))
        
    # Apply transactional filters seamlessly
    if member_filter != "All Members":
        df = df[df['Member'] == member_filter]
    if project_filter != "All Projects":
        df = df[df['Project'] == project_filter]
    if status_filter != "All Statuses":
        df = df[df['Status'] == status_filter]
        
    # Global Metric Totals
    g_col1, g_col2, g_col3, g_col4, g_col5 = st.columns(5)
    g_col1.metric("RECORDS", len(df))
    g_col2.metric("COMPLETED", len(df[df['Status'] == 'Completed']))
    g_col3.metric("SUMMARIES", len(df[df['Project'] == 'Summaries']))
    g_col4.metric("TOTAL WORDS", f"{int(pd.to_numeric(df['WC'], errors='coerce').fillna(0).sum()):,}")
    g_col5.metric("FILES", 0)
    
    st.markdown("---")
    st.subheader("Aggregated Summary")
    
    if len(df) > 0:
        # Resolve the "None" Project / missing index error row sequence:
        # Step A: Drop rows where project label bindings break down inside schemas
        clean_df = df.dropna(subset=['Project']).copy()
        clean_df = clean_df[clean_df['Project'] != "Select project..."]
        
        # Step B: Establish localized runtime computing columns for proper aggregations
        clean_df['Numeric_WC'] = pd.to_numeric(clean_df['WC'], errors='coerce').fillna(0)
        clean_df['Minutes_Calc'] = clean_df['Duration'].apply(parse_duration_to_minutes)
        
        # Step C: Aggregate group matrices natively through group indexes
        summary_agg = clean_df.groupby(['Member', 'Project']).size().reset_index(name='Records')
        
        # Map sums explicitly down clean index lanes to decouple Audio from Summaries
        wc_sum = clean_df.groupby(['Member', 'Project'])['Numeric_WC'].sum().reset_index()
        duration_sum = clean_df.groupby(['Member', 'Project'])['Minutes_Calc'].sum().reset_index()
        
        summary_agg = summary_agg.merge(wc_sum, on=['Member', 'Project'], how='left')
        summary_agg = summary_agg.merge(duration_sum, on=['Member', 'Project'], how='left')
        
        # Step D: Apply presentation layers cleanly (ensuring blank strings instead of mismatched 0 values)
        def format_wc_display(row):
            return f"{int(row['Numeric_WC'])}" if row['Project'] == "Summaries" else ""
            
        def format_duration_display(row):
            if row['Project'] == "Audio" and row['Minutes_Calc'] > 0:
                return f"{int(row['Minutes_Calc'])}m"
            return ""
            
        summary_agg['Total WC'] = summary_agg.apply(format_wc_display, axis=1)
        summary_agg['Total Audio'] = summary_agg.apply(format_duration_display, axis=1)
        
        # Build out dynamic cleanly formatted mathematical summation metrics block footer
        grand_total_row = pd.DataFrame([{
            'Member': 'TOTAL',
            'Project': '',
            'Records': summary_agg['Records'].sum(),
            'Total WC': f"{int(clean_df['Numeric_WC'].sum())}",
            'Total Audio': f"{int(clean_df['Minutes_Calc'].sum())}m" if clean_df['Minutes_Calc'].sum() > 0 else ""
        }])
        
        final_summary_view = pd.concat([summary_agg[['Member', 'Project', 'Records', 'Total WC', 'Total Audio']], grand_total_row], ignore_index=True)
        st.dataframe(final_summary_view, use_container_width=True)
        
        # Safe openpyxl Export Action Component
        try:
            excel_data = generate_excel_report(final_summary_view)
            st.download_button(
                label="📥 Download Excel Performance Report",
                data=excel_data,
                file_name=f"Performance_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Excel generation stalled runtime context. Trace parameters: {e}")
    else:
        st.info("No current transactional logs match applied filter criteria targets.")

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Team details", "Upload task", "View reports"])
    
    st.sidebar.markdown("---")
    st.sidebar.caption("⚡ Rawi Team App Engine V2.1")
    
    if page == "Team details":
        team_details_page()
    elif page == "Upload task":
        upload_task_page()
    elif page == "View reports":
        reports_page()

if __name__ == "__main__":
    st.set_page_config(page_title="Rawi Team Performance Tracker", layout="wide", page_icon="📊")
    main()
