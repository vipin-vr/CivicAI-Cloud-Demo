# PROJECT SPECIFICATION – CivicAI

**Project Name:** CivicAI
**Project Type:** AI-Powered Web Application
**Hackathon:** IDEA//FORGE
**Track:** Track 1 – Civic Pulse, Digital Governance & Public Information

## 1. Project Overview

CivicAI is an AI-powered civic complaint management platform that helps citizens report public problems such as potholes, garbage accumulation, water leakage, broken streetlights and drainage issues.

Citizens can upload photographs and provide location details. AI analyzes the complaint, identifies the problem, suggests its severity and recommends the responsible department.

Administrators can view complaints, manage their priorities and update their status.

## 2. Main Objectives

- Make civic complaint reporting easy.
- Use AI to identify civic problems from images.
- Automatically categorize complaints.
- Prioritize serious public issues.
- Detect possible duplicate complaints.
- Provide complaint tracking and an admin dashboard.

## 3. Technology Stack

- **Frontend:** Streamlit
- **Backend:** Python
- **Database:** SQLite
- **AI:** Google Gemini API (image and text analysis)
- **Charts:** Plotly
- **Image Processing:** Pillow

Keep the application simple and easy to run locally.

## 4. User Roles

There are two main user roles:

**Citizen**
- Submit complaints.
- Upload problem photographs.
- Enter location and description.
- View complaint ID.
- Track complaint status.

**Administrator**
- View all complaints.
- Filter complaints by category and priority.
- View AI-generated analysis.
- Update complaint status.
- View dashboard statistics.

For the initial prototype, use a simple admin login configured through environment variables.

## 5. Main Application Modules

### Module 1: Home Dashboard

Display:
- Total complaints.
- Pending complaints.
- In-progress complaints.
- Resolved complaints.
- Recent complaints.
- Complaint category statistics.

### Module 2: Submit Complaint

Create a complaint form containing:
- Citizen name.
- Problem category.
- Problem description.
- Location or landmark.
- Photograph upload.

Supported categories:
- Pothole / Damaged Road.
- Garbage Accumulation.
- Water Leakage.
- Broken Streetlight.
- Drainage Problem.
- Other.

After submission:
- Generate a unique complaint ID.
- Save complaint information in SQLite.
- Save the uploaded image.
- Display a successful submission message.

### Module 3: AI Complaint Analysis

Use Gemini API to analyze uploaded images and descriptions.

AI should return:
- Detected problem.
- Complaint category.
- Generated complaint description.
- Severity level.
- Suggested responsible department.
- Public safety risk.
- Explanation of the analysis.

Severity levels:
- Low
- Medium
- High
- Critical

If the AI API fails, allow manual complaint submission and category selection.

### Module 4: Priority Scoring

Calculate a priority score from 0 to 100.

Use this formula:

Priority Score = (Severity × 0.4) + (Public Risk × 0.3) + (Public Impact × 0.3)

Each input should be between 0 and 100.

Priority labels:
- 0–29: Low
- 30–49: Medium
- 50–74: High
- 75–100: Critical

Display the score and explain why the complaint received that priority.

### Module 5: Duplicate Complaint Detection

Check whether a similar complaint already exists.

Compare:
- Complaint category.
- Location.
- Complaint description.

Flag possible duplicates for administrator review.

Do not automatically delete duplicate complaints.

### Module 6: Complaint Tracking

Each complaint must have:
- Unique complaint ID.
- Submission date.
- Category.
- Location.
- Priority.
- Current status.

Complaint statuses:
- Submitted
- In Progress
- Resolved

Citizens should be able to search using their complaint ID.

### Module 7: Admin Dashboard

Create an administrator page with:
- All complaints.
- Search by complaint ID.
- Filter by category.
- Filter by priority.
- Filter by status.
- View uploaded photographs.
- View AI analysis.
- Update complaint status.
- View charts using Plotly.

## 6. Database Structure

Create an SQLite database named `civicai.db`.

Create a complaints table containing:

- id
- complaint_id
- citizen_name
- category
- description
- location
- image_path
- ai_analysis
- severity
- public_risk
- public_impact
- priority_score
- priority_label
- suggested_department
- duplicate_flag
- status
- created_at
- updated_at

Use proper database queries and parameterized SQL statements.

## 7. User Interface Design

Design a modern, clean and professional interface.

Theme:
- Primary color: Dark blue.
- Secondary color: Green.
- Background: Light grey or white.
- Simple navigation sidebar.
- Clear buttons and readable text.
- Responsive layout.

Application pages:
1. Home Dashboard.
2. Submit Complaint.
3. Track Complaint.
4. Admin Dashboard.

## 8. Security and Validation

- Store API keys in a `.env` file.
- Never expose API keys in frontend code.
- Validate uploaded image formats and file sizes.
- Validate user inputs.
- Use parameterized SQL queries.
- Protect administrator access.
- Do not expose sensitive citizen information publicly.
- Handle missing API keys and API failures gracefully.

## 9. Project Structure

Create a modular project structure:

CivicAI/
- app.py
- database.py
- ai_analysis.py
- priority.py
- duplicate_detection.py
- requirements.txt
- .env.example
- .gitignore
- pages/
  - 1_Submit_Complaint.py
  - 2_Track_Complaint.py
  - 3_Admin_Dashboard.py
- uploads/
- README.md

## 10. Development Requirements

Build the project in stages:

**Stage 1:** Application interface and SQLite database.

**Stage 2:** Complaint submission and image upload.

**Stage 3:** Gemini AI image analysis.

**Stage 4:** Priority scoring and duplicate detection.

**Stage 5:** Complaint tracking and admin dashboard.

**Stage 6:** Testing, bug fixing and documentation.

Do not attempt to build everything in one step.

After completing each stage:
- Check for errors.
- Run the application.
- Test the implemented features.
- Explain the files created or modified.

## 11. Expected Final Output

The final application should allow a citizen to:

1. Open CivicAI.
2. Submit a civic complaint with a photograph.
3. Receive AI-generated complaint analysis.
4. Receive a priority score.
5. Get a unique complaint ID.
6. Track the complaint.

The administrator should be able to:

1. Log in.
2. View all complaints.
3. Review AI analysis and priority.
4. Identify possible duplicate complaints.
5. Update complaint status.
6. View complaint statistics.

## 12. Important Scope Limitations

- This is a hackathon prototype.
- Do not integrate with actual government portals.
- Do not claim complaints are officially submitted to government authorities.
- Do not build unnecessary features outside this specification.
- Prioritize a working application over complex design.
- AI-generated classifications and priority scores must be treated as recommendations requiring human verification.

**Final Goal:** Build a functional, reliable and professional AI-powered civic complaint management prototype suitable for a live hackathon demonstration.
