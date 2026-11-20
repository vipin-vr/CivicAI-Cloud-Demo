"""CivicAI's public landing page and live civic-complaint overview."""
from __future__ import annotations

import streamlit as st

from database import category_counts, dashboard_counts, get_complaints, initialize_database


st.set_page_config(page_title="CivicAI | Civic issues, made visible", page_icon="🏙️", layout="wide")
initialize_database()

st.markdown(
    """
    <style>
      .stApp { background: radial-gradient(circle at 93% 3%, #d9f7fc 0, transparent 21rem), #f6f9fc; color: #17324d; }
      .block-container { max-width: 1180px; padding-top: 1.25rem; padding-bottom: 2rem; }
      h1, h2, h3 { color: #0d355f; letter-spacing: -0.035em; }
      h2 { font-size: clamp(1.7rem, 3vw, 2.45rem); }
      .brand { font-size: 1.5rem; font-weight: 850; color: #0d355f; margin: 0.25rem 0; }
      .brand span { color: #0b9fbd; }
      [data-testid="stPageLink"] a, [data-testid="stLinkButton"] a { border-radius: 10px; font-weight: 650; transition: all .2s ease; }
      [data-testid="stPageLink"] a:hover, [data-testid="stLinkButton"] a:hover { background: #e7f7fb; color: #087a97; transform: translateY(-1px); }
      [data-testid="stPageLink"] a[aria-current="page"] { color: #087a97; background: #dff6fb; }
      .hero { background: linear-gradient(122deg, #073867 0%, #0a598e 56%, #0b9fbd 135%); border-radius: 28px; color: white; padding: clamp(2rem, 5vw, 4.7rem); margin: 1rem 0 2rem; box-shadow: 0 22px 48px rgba(13, 66, 112, .24); overflow: hidden; position: relative; }
      .hero:before { content: ""; position: absolute; inset: 0; opacity: .24; background-image: radial-gradient(#b7f4ff 1px, transparent 1px); background-size: 24px 24px; mask-image: linear-gradient(90deg, transparent, black); }
      .hero-grid { position: relative; z-index: 1; display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(260px, .85fr); gap: 2rem; align-items: center; }
      .hero h1 { color: white; font-size: clamp(2.35rem, 5vw, 4.5rem); line-height: 1.02; margin-bottom: 1rem; }
      .hero p { color: #e4f7fc; font-size: 1.16rem; max-width: 680px; line-height: 1.65; }
      .eyebrow { color: #0b9fbd; font-weight: 800; font-size: .8rem; letter-spacing: .12em; text-transform: uppercase; }
      .hero .eyebrow { color: #a9effc; }
      .section-intro { max-width: 700px; color: #557086; margin-bottom: 1.5rem; }
      .city-preview { min-height: 285px; padding: 1.15rem; border: 1px solid rgba(197, 246, 255, .45); background: linear-gradient(145deg, rgba(255,255,255,.17), rgba(202,245,253,.04)); border-radius: 20px; backdrop-filter: blur(8px); box-shadow: inset 0 1px rgba(255,255,255,.18); }
      .preview-top { display: flex; gap: .5rem; align-items: center; color: #d9f9ff; font-size: .78rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
      .pulse { width: .55rem; height: .55rem; background: #6df0cc; border-radius: 50%; box-shadow: 0 0 0 5px rgba(109,240,204,.17); }
      .preview-chart { margin: 1.5rem 0 1.1rem; display: flex; align-items: end; gap: .55rem; height: 108px; border-bottom: 1px solid rgba(218,248,252,.35); }
      .preview-bar { flex: 1; border-radius: 7px 7px 2px 2px; background: linear-gradient(#83ecf8, #24acd0); box-shadow: 0 0 15px rgba(99,234,247,.25); }
      .preview-label { color: #c5f5fb; font-size: .78rem; }
      .preview-status { display: grid; grid-template-columns: 1fr 1fr; gap: .7rem; margin-top: 1rem; }
      .preview-chip { border-radius: 12px; padding: .72rem; background: rgba(0, 24, 65, .23); color: #dffbff; font-size: .78rem; }
      .preview-chip b { display: block; color: white; font-size: 1.1rem; margin-top: .2rem; }
      .step, .feature-card, .about-card { background: rgba(255,255,255,.94); border: 1px solid #dceaf3; border-radius: 18px; padding: 1.45rem; box-shadow: 0 8px 20px rgba(19, 61, 97, .06); height: 100%; box-sizing: border-box; transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease; }
      .step:hover, .feature-card:hover { transform: translateY(-5px); border-color: #9edfe9; box-shadow: 0 16px 30px rgba(19, 86, 125, .13); }
      .step-number { display: inline-flex; align-items: center; justify-content: center; width: 2rem; height: 2rem; background: #e1f7fb; color: #067f9c; border-radius: 50%; font-weight: 800; margin-bottom: .75rem; }
      .feature-icon { display: grid; place-items: center; width: 2.85rem; height: 2.85rem; background: linear-gradient(145deg, #e3faff, #d3f2f8); border-radius: 12px; font-size: 1.4rem; margin-bottom: .8rem; }
      .feature-card h3, .step h3 { margin: .15rem 0 .45rem; font-size: 1.08rem; }
      .feature-card p, .step p, .about-card p { color: #557086; line-height: 1.55; margin-bottom: 0; }
      .live-panel { background: linear-gradient(135deg, #e9f9fc, #f7fdfe); border: 1px solid #ccecf4; border-radius: 24px; padding: clamp(1.35rem, 3vw, 2.3rem); margin: 3.5rem 0; }
      [data-testid="stMetric"] { background: white; border: 1px solid #d5eaf1; border-radius: 16px; padding: 1rem; box-shadow: 0 8px 18px rgba(21, 91, 121, .08); }
      [data-testid="stMetricLabel"] { color: #557086; font-weight: 700; }
      [data-testid="stMetricValue"] { color: #087d9a; font-weight: 800; }
      .final-cta { background: linear-gradient(106deg, #062e57, #096b97 68%, #08a2b6); border-radius: 24px; padding: clamp(2rem, 4vw, 3.2rem); color: white; text-align: center; box-shadow: 0 18px 34px rgba(9, 87, 130, .2); }
      .final-cta h2 { color: white; margin: .25rem 0 .75rem; }
      .final-cta p { color: #d9f8fb; max-width: 650px; margin: 0 auto; line-height: 1.6; }
      .footer { border-top: 1px solid #dce7ee; margin-top: 4rem; padding-top: 1.75rem; color: #61798d; font-size: .9rem; }
      @media (max-width: 700px) { .block-container { padding-left: 1rem; padding-right: 1rem; } .hero { border-radius: 18px; } .hero-grid { grid-template-columns: 1fr; } .city-preview { min-height: 220px; } }
    </style>
    """,
    unsafe_allow_html=True,
)

# The normal multipage sidebar remains enabled; these links surface citizen routes on the homepage.
brand, home, submit, track, about = st.columns([2.8, 1, 1.45, 1.25, 1.2])
with brand:
    st.markdown('<div class="brand">🏙️ Civic<span>AI</span></div>', unsafe_allow_html=True)
with home:
    st.page_link("app.py", label="Home")
with submit:
    st.page_link("pages/1_Submit_Complaint.py", label="Submit Complaint")
with track:
    st.page_link("pages/2_Track_Complaint.py", label="Track Complaint")
with about:
    st.link_button("About CivicAI", "#about-civicai", use_container_width=True)

st.markdown("""
<section class="hero"><div class="hero-grid"><div><div class="eyebrow">A clearer path from concern to action</div>
<h1>Your City. Your Voice. Your Change.</h1>
<p>Report civic issues, understand their priority through AI-powered analysis, and track your complaint transparently.</p></div>
<div class="city-preview"><div class="preview-top"><span class="pulse"></span> Civic pulse overview</div>
<div class="preview-chart"><div class="preview-bar" style="height:42%"></div><div class="preview-bar" style="height:67%"></div><div class="preview-bar" style="height:54%"></div><div class="preview-bar" style="height:84%"></div><div class="preview-bar" style="height:70%"></div></div>
<div class="preview-label">A privacy-conscious view of civic activity</div><div class="preview-status"><div class="preview-chip">Report status<b>Visible</b></div><div class="preview-chip">Human review<b>Built in</b></div></div></div></div></section>
""", unsafe_allow_html=True)

primary_cta, secondary_cta, _ = st.columns([1.25, 1.25, 5.5])
with primary_cta:
    st.page_link("pages/1_Submit_Complaint.py", label="Report an Issue", icon="📝", use_container_width=True)
with secondary_cta:
    st.page_link("pages/2_Track_Complaint.py", label="Track Complaint", icon="🔎", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="eyebrow">Simple by design</div>', unsafe_allow_html=True)
st.header("How CivicAI works")
st.markdown('<p class="section-intro">A straightforward, transparent workflow for reporting public issues and keeping citizens informed.</p>', unsafe_allow_html=True)
steps = [
    ("1", "Report an Issue", "Share the issue, its location, and an optional photograph through a guided complaint form."),
    ("2", "AI Analyses the Complaint", "CivicAI suggests a category, severity, priority, and responsible department for human review."),
    ("3", "Track Your Complaint", "Use your complaint ID and private tracking token to check the current status."),
]
for column, (number, title, description) in zip(st.columns(3), steps):
    with column:
        st.markdown(f'<div class="step"><div class="step-number">{number}</div><h3>{title}</h3><p>{description}</p></div>', unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('<div class="eyebrow">Built for clarity</div>', unsafe_allow_html=True)
st.header("Tools for more transparent civic reporting")
features = [
    ("✨", "AI-powered analysis", "Image and text analysis provide structured suggestions while keeping human review in the loop."),
    ("⚡", "Priority assessment", "A transparent scoring model helps identify reports that may need quicker attention."),
    ("🔁", "Duplicate detection", "Similar reports are flagged for review, helping administrators identify recurring concerns."),
    ("🔐", "Private complaint tracking", "Tracking IDs and private tokens let citizens check updates without exposing reports publicly."),
    ("✓", "Administrative review", "Administrators can confirm recommendations, update status, and review reports in one place."),
]
for row in (features[:3], features[3:]):
    for column, (icon, title, description) in zip(st.columns(len(row)), row):
        with column:
            st.markdown(f'<div class="feature-card"><div class="feature-icon">{icon}</div><h3>{title}</h3><p>{description}</p></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

st.markdown('<div id="about-civicai" class="eyebrow">About CivicAI</div>', unsafe_allow_html=True)
st.header("Making civic complaint management easier to understand")
st.markdown('<div class="about-card"><p>CivicAI is a civic-tech prototype that helps citizens document public issues and gives administrators a clearer way to review them. It combines structured reporting, AI-assisted recommendations, priority guidance, and secure tracking to make the complaint process more transparent.</p></div>', unsafe_allow_html=True)

# These are real local application values, not simulated public-service statistics.
st.markdown('<div class="live-panel">', unsafe_allow_html=True)
st.markdown('<div class="eyebrow">Live prototype overview</div>', unsafe_allow_html=True)
st.subheader("Complaint activity")
counts = dashboard_counts()
for column, label in zip(st.columns(4), ["Total", "Submitted", "In Progress", "Resolved"]):
    with column:
        st.metric(label, counts[label])
recent = get_complaints()[:5]
if recent:
    st.markdown("#### Recent reports")
    st.dataframe([{"Complaint ID": c["complaint_id"], "Category": c["category"], "Priority": c["priority_label"], "Status": c["status"]} for c in recent], use_container_width=True, hide_index=True)
else:
    st.info("No complaints have been recorded yet. Use Report an Issue to start.")
stats = category_counts()
if stats:
    import plotly.express as px
    st.plotly_chart(px.bar(stats, x="category", y="count", color="category", title="Complaints by category"), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<section class="final-cta"><div class="eyebrow" style="color:#a9effc">Participate in your city</div><h2>Make Your City Better</h2><p>Document what you see, help make recurring issues visible, and follow your complaint with transparent status updates.</p></section>', unsafe_allow_html=True)
cta_submit, cta_track, _ = st.columns([1.3, 1.3, 5.4])
with cta_submit:
    st.page_link("pages/1_Submit_Complaint.py", label="Report an Issue", icon="📝", use_container_width=True)
with cta_track:
    st.page_link("pages/2_Track_Complaint.py", label="Track a Complaint", icon="🔎", use_container_width=True)

st.markdown('<div class="footer"><strong>CivicAI</strong> &nbsp;·&nbsp; Home &nbsp;·&nbsp; Submit Complaint &nbsp;·&nbsp; Track Complaint<br><br>CivicAI is a demonstration prototype. Complaints are recorded in this application and are not automatically submitted to government authorities.</div>', unsafe_allow_html=True)
