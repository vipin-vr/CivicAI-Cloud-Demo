# CivicAI – AI-Powered Civic Complaint Management

**IDEA//FORGE Hackathon | Track 1 – Civic Pulse, Digital Governance & Public Information**

## About the Project

CivicAI is an AI-powered web application designed to make reporting public problems easier and more accessible.

In many places, problems such as potholes, overflowing garbage, water leakage, broken streetlights and drainage issues can go unnoticed or take too long to address. CivicAI provides a simple platform where citizens can report these problems by submitting a description, location and photograph.

The application uses Google Gemini AI to analyze submitted complaints, identify possible issues and suggest their severity and responsible department. It also helps administrators organize complaints, review priorities and update their status.

The main idea behind CivicAI is simple: make civic problem reporting easier and help bring public issues to attention.

## Live Demo

**Try CivicAI:** https://civicai-cloud-demo.streamlit.app/

## Key Features

- **Easy Complaint Submission:** Citizens can report public problems by entering a description, location and photograph.
- **AI-Powered Analysis:** Google Gemini analyzes complaint details and uploaded images to identify possible civic issues.
- **Automatic Categorization:** Complaints are classified into relevant categories.
- **Priority Assessment:** Each complaint receives a priority score based on its severity, public risk and impact.
- **Duplicate Detection:** The system identifies potentially similar complaints and flags them for administrator review.
- **Complaint Tracking:** Citizens can use their complaint ID to check the current status.
- **Admin Dashboard:** Administrators can review complaints, examine AI analysis, filter records and update complaint statuses.
- **Visual Statistics:** Dashboard charts help administrators understand complaint trends and categories.

## Technology Used

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Web application interface |
| SQLite | Complaint data storage |
| Google Gemini API | AI-based complaint analysis |
| Plotly | Dashboard charts |
| Pillow | Image processing |

## How CivicAI Works

1. A citizen opens the CivicAI application.
2. They select a complaint category and enter the problem description and location.
3. They upload a photograph of the issue.
4. Gemini AI analyzes the available complaint information.
5. The application generates a complaint ID and calculates a priority score.
6. The complaint is stored in the database.
7. The citizen can track the complaint using the complaint ID.
8. The administrator reviews the complaint and updates its status.

## Complaint Categories

CivicAI supports common public issues, including:

- Potholes and damaged roads
- Garbage accumulation
- Water leakage
- Broken streetlights
- Drainage problems
- Other civic issues

## Installation and Setup

Follow these steps to run CivicAI on your local computer.

**1. Clone the repository**

```bash
git clone https://github.com/vipin-vr/CivicAI-Cloud-Demo.git
cd CivicAI-Cloud-Demo
```

**2. Create a virtual environment**

```bash
python -m venv venv
```

**3. Activate the virtual environment**

Windows:

```powershell
venv\Scripts\activate
```

**4. Install the required packages**

```bash
pip install -r requirements.txt
```

**5. Configure environment variables**

Create a `.env` file using `.env.example` as a reference.

Add the required Gemini API key and administrator configuration. Keep your actual credentials private and never upload your `.env` file to GitHub.

**6. Run the application**

```bash
streamlit run app.py
```

The application will open in your browser.

## Project Structure

```text
CivicAI/
│
├── app.py
├── database.py
├── ai_analysis.py
├── priority.py
├── duplicate_detection.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── SPEC.md
│
├── pages/
│   ├── 1_Submit_Complaint.py
│   ├── 2_Track_Complaint.py
│   └── 3_Admin_Dashboard.py
│
└── uploads/
```

## Project Scope

CivicAI is developed as a hackathon prototype to demonstrate how AI can support civic complaint management.

It is not connected to official government complaint systems, and submitting a complaint through this application does not mean that it has been officially registered with a government authority.

AI-generated results are suggestions and should be verified by an administrator before decisions are made.

The current cloud deployment is intended for demonstration. Its temporary storage is not suitable for permanent complaint records or production use.

## Future Improvements

Some possible improvements for future versions include:

- Integration with verified government complaint systems.
- Long-term and secure complaint storage.
- Improved AI accuracy for different types of civic problems.
- More detailed complaint analytics.
- Notifications when complaint statuses change.
- Support for multiple languages.

## Hackathon Information

**Project:** CivicAI  
**Hackathon:** IDEA//FORGE  
**Track:** Track 1 – Civic Pulse, Digital Governance & Public Information  
**Project Type:** AI-Powered Web Application

---

*Built with the goal of making civic problem reporting simpler, smarter and more accessible.*
