A clean, practical, beginner-friendly web app for small ops teams to manage rotating standby rosters, shift swaps, and overtime logging — with clear records for HR.

📌 Problem
Our team has rotating standby shifts.

People get sick, take planned leave, or leave/join the company.

We need an easy way to auto-generate a predictable standby schedule that is flexible — we must be able to override shifts as needed.

Everyone must be able to see who’s on standby week-by-week, month-by-month in a clear, modern calendar.

We also need an overtime log: record start/end time, auto-calculate hours, optional issue & resolution notes — then save reports per person, per month, as CSV/PDF for HR. Old logs must auto-archive.

🎯 End Result
✅ See upcoming standby shifts week-by-week, month-by-month
✅ Add or remove people from the rotation anytime
✅ Easily swap or override shifts for sick leave or planned leave
✅ Clean, modern calendar view with color-coded people
✅ Log overtime with:

Start time & end time

Auto-calculated hours

Optional issue description & resolution notes
✅ Save overtime reports per person, per month, in CSV/PDF format, auto-archived
✅ Simple, attractive UI using CoreUI admin template, Bootstrap 5, and FullCalendar.js — easy for non-tech staff to use

🏗️ Tech Stack
Backend: Python 3.11+, Flask (routes & app logic)

Templates: Jinja2 + CoreUI Free Bootstrap Admin Template for modern look

Frontend: FullCalendar.js for interactive calendar, Bootstrap 5 for styling

Data:

roster.json for team & rotation patterns

CSV files for overtime logs

Optional: PDF export with pdfkit or reportlab

Logic:

rotation_manager.py for rotation & overrides

overtime_logger.py for logging, calculating duration, saving files

📁 Project Structure
php
Copy
Edit
standby-overtime-app/
├── app.py                # Flask app with routes: dashboard, calendar, roster, overtime
├── config.py             # App settings & env vars
├── data/
│   └── roster.json       # Team members, rotation pattern, overrides
├── logs/
│   ├── alice/2024-07.csv # Overtime logs per person/month
│   ├── _archive/         # Archived old logs
├── static/
│   ├── coreui/           # CoreUI CSS/JS assets
│   ├── css/              # Any custom tweaks
│   ├── js/               # FullCalendar setup
│   └── img/              # Icons/logos
├── templates/
│   ├── base.html         # CoreUI base layout
│   ├── dashboard.html    # Summary cards, current standby
│   ├── calendar.html     # Interactive calendar
│   ├── roster.html       # Manage people & overrides
│   ├── overtime.html     # Overtime log form & history
├── utils/
│   ├── rotation_manager.py  # Standby logic
│   ├── overtime_logger.py   # Overtime logging & exports
├── requirements.txt      # Python dependencies
└── README.md
🔄 Core Logic Flow
✅ Roster & Rotation
Load roster.json: team_members, rotation_pattern, start_date, overrides

Weekly rotation: auto-cycles through pattern

Overrides: if a specific date has an override, use it

Merge rotation & overrides to produce final calendar data

✅ Calendar
/calendar route:

Uses rotation_manager.py to generate standby schedule for month

Passes data as JSON to FullCalendar.js

Events color-coded by standby person

FullCalendar uses Bootstrap theme to match CoreUI

✅ Roster Management
/roster route:

Add/remove team members

Add overrides for planned leave/sick days

Updates roster.json safely

✅ Overtime Logging
/overtime route:

Form: start time, end time, optional issue/notes

Auto-calculates duration in hours

Saves to logs/{person}/{YYYY-MM}.csv

Archives older logs automatically

Optional: export logs to PDF

✅ Dashboard
/dashboard route:

Uses CoreUI cards to show:

Current standby person

Next standby person

Total overtime hours logged this month

Recent overrides

🎨 UI Design
✔ Modern & responsive: CoreUI Free Bootstrap Admin Template
✔ Interactive calendar: FullCalendar.js with Bootstrap styling
✔ Clean forms: Bootstrap components for forms & tables
✔ Consistent look: CoreUI sidebar, nav, icons

🔧 Configuration
Create a .env file:

env
Copy
Edit
FLASK_SECRET_KEY=your-secret-key
DATABASE_PATH=data/roster.json
LOG_DIRECTORY=logs/
DEFAULT_ROTATION_DAYS=7
📝 Development & Prompts
Build the app step by step. Use these task prompts for Cursor:

“Generate Flask routes for /dashboard, /calendar, /roster, /overtime”

“Create base.html using CoreUI sidebar/nav with {% block content %}”

“Create rotation_manager.py with load_roster() and get_standby_person()”

“Create calendar.html using FullCalendar with Bootstrap theme”

“Generate overtime_logger.py that saves logs to CSV and auto-archives”

✅ What “Done” Looks Like
✔ Predictable rotation schedule auto-updates
✔ Flexible overrides for leave/sick days
✔ Clear calendar view for team
✔ Easy overtime logging with proof
✔ Nice-looking UI everyone is comfortable using
✔ All data versioned and archived for HR

📈 Future Enhancements
Email or Slack notifications for shift changes

Integration with Google Calendar export (.ics)

Authentication with user roles (admin/user)

Mobile-friendly tweaks for on-call people on the move

Built with ❤️ to make standby rosters & overtime logging simple, clear, and human-friendly.

🔑 Pro Tip for Cursor
When using AI code generation:

Work file-by-file, one clear function at a time.

Always provide JSON/CSV samples so the AI knows your data shapes.

Test logic (like rotation) before wiring it to routes & templates.

Keep TODO.md up to date so you stay on track.

