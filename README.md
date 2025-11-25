# Client Metadata App

A lightweight CRM-style web app for sales reps who juggle many clients (e.g., insurance or hardware reps). It keeps a simple, searchable list of clients with explicit **Go** and **No-Go** fields so you always know what moves a deal forward or blocks it (e.g., “client only wants orange iPhone 17 Pro”).

## Stack

- Flask + SQLite (stored locally as `client_data.db`)
- Vanilla JS + fetch API for a minimal UI

## Setup

1. Create a virtualenv (optional but recommended):
   ```bash
   python -m venv .venv
   .venv\\Scripts\\activate  # Windows
   source .venv/bin/activate # macOS/Linux
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app (will auto-create the database):
   ```bash
   flask --app app run --debug
   ```
   Then open http://127.0.0.1:5000.

You can also run `python app.py` to start the development server.

## Features

- Capture core client details plus **Go** (green lights) and **No-Go** (blockers/non-negotiables) notes.
- Inline editing/deleting of clients, with filters by status and quick search.
- “Delete database” button (with confirmation) to clear all records and restart fresh.
- SQLite-backed API endpoints:
  - `GET /api/clients` list all clients
  - `POST /api/clients` create
  - `PUT /api/clients/<id>` update
  - `DELETE /api/clients/<id>` remove
  - `POST /api/reset-db` clear all records (leaves the SQLite file in place)

## Ship as a double-clickable app (Windows)

For business users without Python, build a single `.exe` that opens the app and browser automatically:

1. Install PyInstaller in your dev environment: `pip install pyinstaller`
2. Build:  
   ```bash
   pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" app.py
   ```
3. Share `dist/app.exe` along with the `templates` and `static` folders (PyInstaller bundles them into the exe). When someone double-clicks `app.exe`, it starts the server, opens their browser to the app, and stores `client_data.db` next to the exe.

Tip: Zip the `dist` folder for distribution so non-technical users can just unzip and double-click `app.exe`.

## Notes

- The database file `client_data.db` is ignored by git for local use. Back it up or move to a managed database if you deploy.
