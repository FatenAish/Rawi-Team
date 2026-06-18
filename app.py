import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Initialize database session state layout architecture if not present
if 'tasks_db' not in st.session_state:
    st.session_state.tasks_db = pd.DataFrame([
        {
            "Date": "2026-06-17",
            "Member": "Faten Aish",
            "Project": "Summaries",
            "Item Name": "مقدمة: الزَّوَاجُ فِي بَيْتِ النُّبُوَّةِ",
            "Resource Link": "https://example.com/summary1",
            "Status": "Completed",
            "WC": 2444,
            "Duration": None
        },
        {
            "Date": "2026-06-17",
            "Member": "Yazan Dmara",
            "Project": "Audio",
            "Item Name": "مقدمة: الزَّوَاجُ فِي بَيْتِ النُّبُوَّةِ",
            "Resource Link": "https://example.com/audio1",
            "Status": "Completed",
            "WC": None,
            "Duration": "00:07:00"
        }
    ])

def parse_duration_to_minutes(duration_str):
    if pd.isna(duration_str) or not duration_str or str(duration_str).strip().lower() in ['none', '']:
        return 0
    try:
        parts = list(map(int, str(duration_str).split(':')))
        if len(parts) == 3:
            return parts[0] * 60 + parts[1] + parts[2] / 60
        elif len(parts) == 2:
            return parts[0] + parts[1] / 60
    except Exception:
        return 0
    return 0

def generate_excel_report(report_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        report_df.to_excel(writer, index=False, sheet_name='Performance Summary')
    return output.getvalue()

def upload_task_page():
    st.title("Upload task")
    st.caption("Record a new task context matrix profile for a team member")
    
    col1, col2 = st.columns(2)
    with col1:
        member = st.selectbox("TEAM MEMBER", ["Faten Aish", "Yazan Dmara", "Kamal Arslan", "Nour Aldeen", "Doha Alrefai", "Ali"])
        status = st.selectbox("STATUS", ["Select status...", "Uploaded", "Completed", "In Progress"], index=0)
    with col2:
        date_val = st.date_input("DATE", datetime(2026, 6, 17))
        project = st.selectbox("PROJECT", ["Select project...", "Summaries", "Audio", "Other Tasks"], index=0)
        
    st.markdown("---")
    
    # Structural Reset Hooks to isolate parameters cleanly
    item_name = ""
    resource_link = ""
    wc_value = None
    duration_value = None
    submit_disabled = False

    if project == "Select project...":
        st.info("Select a project type above. The relevant task fields will appear here.")
        submit_disabled = True
        
    elif project == "Summaries":
        st.markdown("### 📝 Summaries Configuration Frame")
        item_name = st.text_input("Summary Name", placeholder="Enter the summary title here...")
        resource_link = st.text_input("Link", placeholder="Paste the text resource link address...")
        wc_value = st.number_input("Word Count (WC)", min_value=0, step=1, value=0)
        duration_value = None  # Strict clear

    elif project == "Audio":
        st.markdown("### 🎧 Audio Configuration Frame")
        item_name = st.text_input("Audio Name", placeholder="Enter track recording target label...")
        resource_link = st.text_input("Link", placeholder="Paste cloud directory storage shared resource url...")
        duration_input = st.text_input("Duration (Format: hh:mm:ss or mm:ss)", value="00:00:00")
        duration_value = duration_input if duration_input != "00:00:00" else None
        wc_value = None  # Strict clear
        
    else:
        st.markdown("### ⚙️ General Task Context")
        item_name = st.text_input("Task Label / Name")
        resource_link = st.text_input("Reference Link")

    st.markdown("##")
    if st.button("✨ Save task", disabled=submit_disabled):
        if status == "Select status...":
            st.error("Please assign a structural status tag value to complete log storage initialization.")
        elif not item_name.strip():
            st.error("Please supply an identifying Name metric for this entry asset.")
        else:
            new_row = {
                "Date": date_val.strftime("%Y-%m-%d"),
                "Member": member,
                "Project": project,
                "Item Name": item_name,
                "Resource Link": resource_link,
                "Status": status,
                "WC": wc_value,
                "Duration": duration_value
            }
            st.session_state.tasks_db = pd.concat([st.session_state.tasks_db, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Successfully saved {project} record asset ledger reference entry row path updates!")

def team_details_page():
    st.title("Team details")
    selected_member = st.sidebar.selectbox("Select Target Scope View", ["Faten Aish", "Yazan Dmara", "Kamal Arslan", "Nour Aldeen", "Doha Alrefai", "Ali"])
    
    member_df = st.session_state.tasks_db[st.session_state.tasks_db['Member'] == selected_member].copy()
    
    # Dash KPIs Metrics Calculations
    total_records = len(member_df)
    completed_records = len(member_df[member_df['Status'] == 'Completed'])
    summaries_count = len(member_df[member_df['Project'] == 'Summaries'])
    total_words = int(pd.to_numeric(member_df['WC'], errors='coerce').fillna(0).sum())
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("RECORDS", total_records)
    m_col2.metric("COMPLETED", completed_records)
    m_col3.metric("SUMMARIES", summaries_count)
    m_col4.metric("TOTAL WORDS", f"{total_words:,}")
    
    st.markdown("##")
    if total_records > 0:
        display_df = member_df.copy()
        display_df['WC'] = display_df['WC'].apply(lambda x: f"{int(x)}" if pd.notna(x) else "")
        display_df['Duration'] = display_df['Duration'].fillna("")
        st.dataframe(display_df[["Date", "Project", "Item Name", "Resource Link", "Status", "WC", "Duration"]], use_container_width=True)
    else:
        st.info("No matching logging activity sequence found for user space domain reference pipeline mapping values.")

def reports_page():
    st.title("Performance Reports")
    df = st.session_state.tasks_db.copy()
    
    # Aggregated Summary Processing Loop Core Block Frame
    if len(df) > 0:
        clean_df = df.dropna(subset=['Project']).copy()
        clean_df = clean_df[clean_df['Project'] != "Select project..."]
        
        clean_df['Numeric_WC'] = pd.to_numeric(clean_df['WC'], errors='coerce').fillna(0)
        clean_df['Minutes_Calc'] = clean_df['Duration'].apply(parse_duration_to_minutes)
        
        summary_agg = clean_df.groupby(['Member', 'Project']).size().reset_index(name='Records')
        wc_sum = clean_df.groupby(['Member', 'Project'])['Numeric_WC'].sum().reset_index()
        duration_sum = clean_df.groupby(['Member', 'Project'])['Minutes_Calc'].sum().reset_index()
        
        summary_agg = summary_agg.merge(wc_sum, on=['Member', 'Project'], how='left')
        summary_agg = summary_agg.merge(duration_sum, on=['Member', 'Project'], how='left')
        
        # Present context cleanly without crossover contamination values
        summary_agg['Total WC'] = summary_agg.apply(lambda r: f"{int(r['Numeric_WC'])}" if r['Project'] == "Summaries" else "", axis=1)
        summary_agg['Total Audio'] = summary_agg.apply(lambda r: f"{int(r['Minutes_Calc'])}m" if r['Project'] == "Audio" and r['Minutes_Calc'] > 0 else "", axis=1)
        
        st.subheader("Aggregated Dashboard View Summary Ledger Matrix")
        st.dataframe(summary_agg[['Member', 'Project', 'Records', 'Total WC', 'Total Audio']], use_container_width=True)
        
        try:
            excel_bin = generate_excel_report(summary_agg)
            st.download_button("📥 Download Performance Report Worksheet", data=excel_bin, file_name="Performance_Summary.xlsx")
        except Exception as e:
            st.error(f"Excel generation environment hook missing: {e}")

def main():
    st.sidebar.title("Navigation Links Controller")
    page = st.sidebar.radio("Go to view route channel layer path", ["Team details", "Upload task", "View reports"])
    if page == "Team details":
        team_details_page()
    elif page == "Upload task":
        upload_task_page()
    elif page == "View reports":
        reports_page()

if __name__ == "__main__":
    st.set_page_config(page_title="Rawi Project Analytics Hub Module Engine", layout="wide")
    main()
