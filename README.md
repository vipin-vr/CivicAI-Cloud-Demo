# CivicAI

CivicAI is a local Streamlit hackathon prototype for recording, triaging, tracking, and administering civic complaints. It does not submit reports to government systems. AI suggestions and priority scores require human verification.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`, then configure administrator credentials. Add a Gemini key to enable image/text analysis; the app works with a manual-safe fallback when no key is configured.
4. Start: `streamlit run app.py`

The SQLite database (`civicai.db`) and image files are created locally when reports are submitted.

## Pages

- **Home:** live counts, recent reports, category chart.
- **Submit Complaint:** validates reports, saves images, analyzes via Gemini when available, scores priority, and flags possible duplicates.
- **Track Complaint:** allows citizens to retrieve a report by tracking ID.
- **Admin Dashboard:** environment-variable-protected review, filters, charts, AI detail, images, and status updates.
