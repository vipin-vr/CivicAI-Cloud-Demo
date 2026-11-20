from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
import streamlit as st

from ai_analysis import CATEGORIES, analyse_complaint
from database import create_complaint, generate_tracking_token, hash_tracking_token, initialize_database
from duplicate_detection import find_possible_duplicate
from image_uploads import ImageUploadError, sanitize_image, store_sanitized_image
from priority import calculate_priority

initialize_database()
st.title("Submit a Complaint")
st.caption("Your report is recorded in this prototype, not submitted to a government authority.")

with st.form("complaint_form", clear_on_submit=True):
    citizen_name = st.text_input("Your name", max_chars=100)
    category = st.selectbox("Problem category", CATEGORIES)
    description = st.text_area("Describe the problem", max_chars=1000, placeholder="What happened, where exactly, and how long has it been there?")
    location = st.text_input("Location or landmark", max_chars=250)
    image = st.file_uploader("Photograph (optional, JPG/PNG/WebP, max 10 MB)", type=["jpg", "jpeg", "png", "webp"])
    submitted = st.form_submit_button("Submit complaint", type="primary")

if submitted:
    if not all([citizen_name.strip(), description.strip(), location.strip()]):
        st.error("Please provide your name, description, and location.")
        st.stop()
    image_bytes, image_path, mime_type = None, None, None
    if image:
        try:
            sanitized_image = sanitize_image(image.getvalue())
            image_bytes, mime_type = sanitized_image.data, sanitized_image.mime_type
            image_path = str(store_sanitized_image(sanitized_image))
        except ImageUploadError as error:
            st.error(str(error))
            st.stop()
    with st.spinner("Analyzing complaint…"):
        analysis = analyse_complaint(image_bytes, mime_type, description.strip(), category)
    normalized_citizen_category = " ".join(category.casefold().split())
    normalized_ai_category = " ".join(analysis["category"].casefold().split())
    mismatch_flag = int(normalized_citizen_category != normalized_ai_category)
    severity = analysis["severity"]
    score, label, explanation = calculate_priority(severity, analysis["public_risk"], analysis["public_impact"])
    duplicate, related_id = find_possible_duplicate(category, location, description)
    complaint_id = f"CIV-{datetime.now():%Y%m%d}-{uuid.uuid4().hex[:6].upper()}"
    tracking_token = generate_tracking_token()
    now = datetime.now(timezone.utc).isoformat()
    create_complaint({"complaint_id": complaint_id, "citizen_name": citizen_name.strip(), "category": category, "description": description.strip(), "location": location.strip(), "image_path": image_path, "ai_analysis": json.dumps(analysis), "severity": severity, "public_risk": analysis["public_risk"], "public_impact": analysis["public_impact"], "priority_score": score, "priority_label": label, "suggested_department": analysis["suggested_department"], "ai_category": analysis["category"], "ai_generated_description": analysis["generated_description"], "ai_suggested_department": analysis["suggested_department"], "mismatch_flag": mismatch_flag, "duplicate_flag": int(duplicate), "duplicate_complaint_id": related_id, "tracking_token_hash": hash_tracking_token(tracking_token), "status": "Submitted", "created_at": now, "updated_at": now})
    st.success(f"Complaint submitted. Your tracking ID is **{complaint_id}**")
    st.warning("Save this tracking token now. It will not be shown again and cannot be recovered.")
    st.code(tracking_token, language=None)
    st.metric("Priority", f"{label} — {score}/100")
    st.write(explanation)
    if duplicate:
        st.warning(f"This may be similar to {related_id}. It has been flagged for administrator review; your report was still recorded.")
    if mismatch_flag:
        st.warning("The image analysis suggests a different category. An administrator will review the report; your original category was preserved.")
    if not analysis["ai_available"]:
        st.info("AI was unavailable, so your selected category and review defaults were used.")
