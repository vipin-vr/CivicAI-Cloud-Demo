import streamlit as st

from database import decode_analysis, get_complaint_for_tracking, initialize_database

initialize_database()
st.title("Track a Complaint")
complaint_id = st.text_input("Complaint ID", placeholder="CIV-YYYYMMDD-XXXXXX").strip().upper()
tracking_token = st.text_input("Tracking token", type="password")
if st.button("Track complaint", type="primary"):
    complaint = get_complaint_for_tracking(complaint_id, tracking_token)
    if not complaint:
        st.error("Complaint ID or tracking token is invalid.")
    else:
        st.success(f"Status: {complaint['status']}")
        a, b, c = st.columns(3)
        a.metric("Priority", f"{complaint['priority_label']} ({complaint['priority_score']}/100)")
        b.markdown(f"**Category**  \n{complaint['category']}")
        c.markdown(f"**Submitted**  \n{complaint['created_at'][:10]}")
        st.markdown(f"**Location:** {complaint['location']}")
        st.markdown(f"**Description:** {complaint['description']}")
        analysis = decode_analysis(complaint["ai_analysis"])
        with st.expander("AI recommendation"):
            st.write(analysis.get("explanation", "No analysis available."))
            st.markdown(f"**Suggested department:** {complaint['suggested_department'] or 'Pending review'}")
