#  BrainForge AI - Startup Idea Planner & Viability Sandbox

BrainForge AI is a premium, responsive web application built with **Python, Django, and Vanilla CSS** that helps builders, hackathon teams, and entrepreneurs structure vague startup ideas into comprehensive execution blueprints. 

By analyzing constraints such as weekly time commitment, budget, goals, and technical skills, the platform generates dynamic roadmaps, identifies hidden assumptions, assesses risks, and offers an interactive sandbox simulator to run what-if scenarios.

---

##  Advanced Hackathon Features

### 1. BrainForge Readiness Score
A weighted scoring engine generating a single overall readiness score out of 100 based on:
* **Skill Readiness (40%)**
* **Time Readiness (30%)**
* **Budget Readiness (20%)**
* **Risk Level (10%)**

It features a circular SVG progress indicator and a dynamic Venture Strategist AI assessment explaining the viability category (*Strong Readiness*, *Moderate Readiness*, or *High Risk*).

### 2. Hidden Assumptions Validator
A grid of color-coded risk cards (Low = Green, Medium = Orange, High = Red) mapping out underlying hypotheses in User, Market, Technical, and Resource domains, providing action-oriented validation steps.

### 3. Scenario Sandbox (What-If Simulator)
An interactive AJAX sandbox playground. Drag sliders to adjust weekly hours, budget, team size, and skill match dynamically to see the overall readiness score, success probabilities, and side-by-side Chart.js charts update instantly.

### 4. ReportLab PDF Exporter
Generates a multi-page PDF report including a custom title page, table representations of feasibility indicators, roadmap milestones, assumptions grids, and disclaimer panels.

### 5. Pitch Demo Mode
A prominent ` Load Hackathon Demo` button on the home dashboard that instantly seeds a rich prototype plan for an **"AI Resume Analyzer"** startup project, populating the entire dashboard database.

### 6. Team Details Widget
An interactive team overview panel at `/team/` and in the navigation dropdown representing team metadata, roles, and profiles.

### 7. BrainForge Coach Context-Aware Chatbot
A floating conversational AI assistant on the project detail page that has complete access to the specific project analysis context (feasibility, risks, milestones, debate recommendations) to answer questions, explain scores, and brainstorm next steps in real-time.

### 8. Premium Dark Theme Switcher
A sun/moon theme toggle button in the top navigation bar to instantly transition between the default premium light theme and a customized deep dark slate theme. Preferences are persisted in `localStorage` and checked in `<head>` to prevent light-theme flashes.

---
## AI Processing Pipeline

BrainForge AI follows a structured reasoning workflow:

1. Collect project inputs
2. Analyze feasibility constraints
3. Calculate readiness score
4. Detect hidden assumptions
5. Identify project risks
6. Simulate future scenarios
7. Generate execution roadmap
8. Recommend first action
9. Enable interactive coaching via BrainForge Coach
10. Export comprehensive PDF reports

---
## Responsible AI

### Risk
Users may over-rely on AI-generated recommendations.

### Mitigation
- Confidence indicators
- Multiple scenario simulations
- Explicit uncertainty communication
- Human-in-the-loop decision making

### Human Control
BrainForge AI never decides whether a user should pursue a project.

The final decision remains entirely with the user.

---
## Future Enhancements

- User authentication
- Multi-project workspace
- Team collaboration
- Industry-specific planning templates
- Advanced analytics dashboards
- Mobile application
- Historical decision tracking

---

##  Local Setup & Setup Instructions

To run the application locally on your system, follow the steps below:

### 1. Clone & Setup Project
```bash
# Navigate to project folder
cd "BrainForge AI"

# Create a Python virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Local Settings
Create a `.env` file in the root directory and add the following secrets:
```env
# secret key can be anything for local development
SECRET_KEY=your_secret_key_here
DEBUG=True

# Obtain your Google Gemini API Key from: https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run Database Migrations
Initialize the SQLite database:
```bash
python manage.py migrate
```

### 4. Run Development Server
```bash
python manage.py runserver
```
Open **`http://127.0.0.1:8000/`** in your browser.

---

##  Testing & Verification

We have implemented a comprehensive test suite covering models, mock fallbacks, views, and view calculations.

To run the automated tests:
```bash
python manage.py test planner
```

Output:
```text
Found 15 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
...............
----------------------------------------------------------------------
Ran 15 tests in 1.855s

OK
Destroying test database for alias 'default'...
```

---

##  Technology Stack
- **Backend**: Python 3.11, Django 4.2
- **AI Models**: Google Gemini API (`gemini-3.5-flash`) with high-fidelity local mock fallbacks
- **Libraries**: ReportLab, Pillow, python-dotenv
- **Frontend**: HTML5, Vanilla CSS (CSS Grid, Flexbox, transitions), Chart.js
