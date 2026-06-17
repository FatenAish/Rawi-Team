def team_details_page(df: pd.DataFrame) -> None:
    st.markdown("<div class='page-title'>Team details</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='page-subtitle'>Performance records for <b>{st.session_state.selected_member}</b></div>", unsafe_allow_html=True)
    
    member_df = df[df["member"] == st.session_state.selected_member].copy() if not df.empty else df

    if not member_df.empty:
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            date_filter = st.selectbox("DATE FILTER", ["All Time", "Today", "This Week", "Last Week", "This Month", "Custom Range"], key="td_date")
        
        start_date = None
        end_date = None
        
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
        st.info(f"No records found for {st.session_state.selected_member} in the selected date range.")
        return

    # --- TABLE FORMATTING LOGIC ---
    table_df = member_df.copy()
    table_df["Date"] = table_df["task_date"].apply(lambda x: x.strftime("%b %d, %Y") if pd.notna(x) else "")
    table_df["Project"] = table_df["project"].fillna("")
    
    # Map 'title' to 'Details' if it exists, otherwise use 'details' text
    table_df["Details"] = table_df.apply(lambda r: str(r.get("title") or "") if str(r.get("title") or "").strip() else str(r.get("details") or "")[:80], axis=1)
    table_df["Status"] = table_df["status"].fillna("")
    
    # Strictly enforce blank cells for irrelevant metrics (replaces 'None' or '0' with "")
    table_df["WC"] = table_df.apply(lambda r: int(r["word_count"]) if r["Project"] == "Summaries" and pd.notna(r["word_count"]) and r["word_count"] > 0 else "", axis=1)
    table_df["Duration"] = table_df.apply(lambda r: str(r["duration"]) if r["Project"] == "Audio" and pd.notna(r["duration"]) and str(r["duration"]).strip() not in ["None", ""] else "", axis=1)
    
    display_cols = ["Date", "Project", "Details", "Status", "WC", "Duration"]
    table_df = table_df[display_cols]

    # Calculate Totals exclusively for their respective projects
    total_wc = member_df[member_df["project"] == "Summaries"]["word_count"].sum()
    total_dur_mins = sum(member_df[member_df["project"] == "Audio"]["duration"].apply(parse_duration_to_minutes))

    total_row = pd.DataFrame([{
        "Date": "TOTAL",
        "Project": "",
        "Details": "",
        "Status": "",
        "WC": int(total_wc) if total_wc > 0 else "",
        "Duration": format_duration(total_dur_mins) if total_dur_mins > 0 else ""
    }])

    final_df = pd.concat([table_df, total_row], ignore_index=True)

    # Note: Removed 'column_config' for WC to allow empty strings ("") without Streamlit throwing a type error
    st.dataframe(
        final_df,
        hide_index=True,
        use_container_width=True,
    )
