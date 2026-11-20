from __future__ import annotations

import secrets

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from admin_auth import authenticate_admin, resolve_client_identifier
from ai_analysis import CATEGORIES, DEPARTMENTS
from database import category_counts, decode_analysis, get_complaints, initialize_database, update_complaint_review_and_status
from image_uploads import is_approved_image_path

load_dotenv()
initialize_database()
st.title("Administrator Dashboard")

def logged_in() -> bool:
    if st.session_state.get("admin_authenticated"):
        return True
    with st.form("admin_login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        attempted = st.form_submit_button("Log in", type="primary")
    if attempted:
        session_identifier = st.session_state.setdefault("admin_rate_limit_session", secrets.token_urlsafe(32))
        client = resolve_client_identifier(st.context.headers, session_identifier)
        result = authenticate_admin(username, password, client.value)
        if result.authenticated:
            st.session_state.admin_authenticated = True
            st.rerun()
        st.error(result.message)
    return False

if not logged_in():
    st.info("Administrator credentials must be configured securely for this environment.")
    session_identifier = st.session_state.setdefault("admin_rate_limit_session", secrets.token_urlsafe(32))
    client = resolve_client_identifier(st.context.headers, session_identifier)
    if not client.proxy_verified:
        st.warning("Public deployment warning: a trusted proxy client identifier is not configured or verified. Application-level IP rate limiting is insufficient until the hosting proxy is configured.")
    st.stop()

if st.sidebar.button("Log out"):
    st.session_state.admin_authenticated = False
    st.rerun()

c1, c2, c3, c4 = st.columns(4)
search = c1.text_input("Complaint ID")
category = c2.selectbox("Category", ["All"] + CATEGORIES)
priority = c3.selectbox("Priority", ["All", "Low", "Medium", "High", "Critical"])
status = c4.selectbox("Status", ["All", "Submitted", "In Progress", "Resolved"])
complaints = get_complaints(search, category, priority, status)
st.subheader(f"Complaints ({len(complaints)})")
if complaints:
    frame = pd.DataFrame(complaints)
    st.dataframe(frame[["complaint_id", "category", "location", "severity", "priority_score", "priority_label", "duplicate_flag", "duplicate_complaint_id", "status", "created_at"]], use_container_width=True, hide_index=True)
    st.plotly_chart(px.pie(category_counts(), values="count", names="category", title="Category distribution"), use_container_width=True)
    options = {f"{c['complaint_id']} — {c['category']}": c for c in complaints}
    selected = options[st.selectbox("Review complaint", list(options))]
    st.divider()
    st.subheader(selected["complaint_id"])
    if is_approved_image_path(selected["image_path"]):
        st.image(selected["image_path"], caption="Uploaded photograph", width=420)
    analysis = decode_analysis(selected["ai_analysis"])
    ai_category = selected.get("ai_category") or analysis.get("category") or "Not available"
    ai_description = selected.get("ai_generated_description") or analysis.get("generated_description") or "Not available"
    ai_department = selected.get("ai_suggested_department") or analysis.get("suggested_department") or selected["suggested_department"] or "Not available"
    citizen_column, ai_column = st.columns(2)
    with citizen_column:
        st.markdown("#### Citizen report")
        st.markdown(f"**Selected category:** {selected['category']}")
        st.markdown(f"**Description:** {selected['description']}")
        st.markdown(f"**Location:** {selected['location']}")
    with ai_column:
        st.markdown("#### AI recommendation")
        st.markdown(f"**Detected category:** {ai_category}")
        st.markdown(f"**Generated description:** {ai_description}")
        st.markdown(f"**Suggested department:** {ai_department}")
    if selected.get("mismatch_flag"):
        st.warning("Category mismatch: the AI image analysis differs from the citizen-selected category. Human review is required.")
    if selected["duplicate_flag"]:
        related_id = selected.get("duplicate_complaint_id")
        st.warning(f"Possible duplicate of {related_id} — retain for human review." if related_id else "Possible duplicate — retain for human review.")
    with st.expander("AI analysis", expanded=True):
        st.json(analysis)
    st.subheader("Administrator confirmation")
    category_options = CATEGORIES
    current_category = selected.get("admin_confirmed_category") or selected["category"]
    category_index = category_options.index(current_category) if current_category in category_options else 0
    department_options = list(dict.fromkeys(list(DEPARTMENTS.values()) + [ai_department]))
    current_department = selected.get("admin_confirmed_department") or ai_department
    department_index = department_options.index(current_department) if current_department in department_options else 0
    if selected.get("reviewed_flag"):
        st.caption(f"Reviewed on {selected['reviewed_at'][:10] if selected.get('reviewed_at') else 'an earlier date'}.")
    with st.form(f"review_{selected['complaint_id']}"):
        confirmed_category = st.selectbox("Confirmed category", category_options, index=category_index, key=f"category_{selected['complaint_id']}")
        confirmed_department = st.selectbox("Confirmed department", department_options, index=department_index, key=f"department_{selected['complaint_id']}")
        new_status = st.selectbox("Update status", ["Submitted", "In Progress", "Resolved"], index=["Submitted", "In Progress", "Resolved"].index(selected["status"]), key=f"status_{selected['complaint_id']}")
        save_review = st.form_submit_button("Save review and status", type="primary")
    if save_review:
        if update_complaint_review_and_status(selected["complaint_id"], confirmed_category, confirmed_department, new_status):
            st.success("Administrator review and status saved.")
            st.rerun()
        else:
            st.error("The review could not be saved.")
else:
    st.info("No complaints match the selected filters.")
