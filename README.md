# Corporate Training Program Manager

A Flask-based web application for managing corporate training programs. The system allows users to upload student data via CSV, organize learners into cohorts, and automatically assign them into course sections. It also provides section summary reports to support program administration.

## Features
- Upload student data via CSV
- Automatically assign students to course sections
- Generate section summary reports
- SQLite database integration
- Multi-page web interface

## Tech Stack
- Python
- Flask
- SQLite
- HTML/CSS

## How to Run Locally

1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app

```bash
python app.py
```

4. Open in browser

```text
http://127.0.0.1:5000
```
