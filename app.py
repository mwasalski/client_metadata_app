from __future__ import annotations

import sqlite3
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, jsonify, render_template, request, Response
import csv
import io


def resolve_app_dirs():
    """Resolve paths for packaged (PyInstaller) and dev modes."""
    if hasattr(sys, "_MEIPASS"):
        runtime_dir = Path(sys._MEIPASS)  # temp folder with bundled assets
        base_dir = Path(sys.executable).resolve().parent  # keep DB next to .exe
    else:
        runtime_dir = Path(__file__).resolve().parent
        base_dir = runtime_dir
    return base_dir, runtime_dir


BASE_DIR, RUNTIME_DIR = resolve_app_dirs()
DATABASE = BASE_DIR / "client_data.db"

app = Flask(
    __name__,
    static_folder=str(RUNTIME_DIR / "static"),
    template_folder=str(RUNTIME_DIR / "templates"),
)

def get_db() -> sqlite3.Connection:
    """Open a SQLite connection with Row objects for dict-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the clients table if it does not exist."""
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            company TEXT,
            email TEXT,
            phone TEXT,
            status TEXT DEFAULT 'prospect',
            go_factors TEXT,
            no_go_factors TEXT,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


def row_to_dict(row: sqlite3.Row) -> Dict:
    return {
        "id": row["id"],
        "full_name": row["full_name"],
        "company": row["company"],
        "email": row["email"],
        "phone": row["phone"],
        "status": row["status"],
        "go_factors": row["go_factors"],
        "no_go_factors": row["no_go_factors"],
        "notes": row["notes"],
        "created_at": row["created_at"],
    }


def parse_payload(payload: Dict) -> Dict[str, Optional[str]]:
    """Extract and normalize fields from the request payload."""
    def clean(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    return {
        "full_name": clean(payload.get("full_name")),
        "company": clean(payload.get("company")),
        "email": clean(payload.get("email")),
        "phone": clean(payload.get("phone")),
        "status": clean(payload.get("status")) or "prospect",
        "go_factors": clean(payload.get("go_factors")),
        "no_go_factors": clean(payload.get("no_go_factors")),
        "notes": clean(payload.get("notes")),
    }


def validate_payload(data: Dict[str, Optional[str]]) -> List[str]:
    errors: List[str] = []
    if not data.get("full_name"):
        errors.append("full_name is required.")
    if data.get("status") not in {"prospect", "active", "closed", "churn_risk"}:
        errors.append("status must be one of: prospect, active, closed, churn_risk.")
    return errors


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/clients", methods=["GET"])
def list_clients():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM clients ORDER BY created_at DESC, id DESC"
    ).fetchall()
    conn.close()
    return jsonify([row_to_dict(row) for row in rows])


@app.route("/api/clients", methods=["POST"])
def create_client():
    payload = parse_payload(request.get_json(force=True, silent=True) or {})
    errors = validate_payload(payload)
    if errors:
        return jsonify({"errors": errors}), 400

    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO clients (full_name, company, email, phone, status, go_factors, no_go_factors, notes)
        VALUES (:full_name, :company, :email, :phone, :status, :go_factors, :no_go_factors, :notes)
        """,
        payload,
    )
    conn.commit()
    new_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM clients WHERE id = ?", (new_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row)), 201


@app.route("/api/clients/<int:client_id>", methods=["PUT"])
def update_client(client_id: int):
    payload = parse_payload(request.get_json(force=True, silent=True) or {})
    errors = validate_payload(payload)
    if errors:
        return jsonify({"errors": errors}), 400

    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "Client not found"}), 404

    conn.execute(
        """
        UPDATE clients
        SET full_name = :full_name,
            company = :company,
            email = :email,
            phone = :phone,
            status = :status,
            go_factors = :go_factors,
            no_go_factors = :no_go_factors,
            notes = :notes
        WHERE id = :id
        """,
        {**payload, "id": client_id},
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(updated))


@app.route("/api/clients/<int:client_id>", methods=["DELETE"])
def delete_client(client_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "Client not found"}), 404

    conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()
    return jsonify({"deleted": client_id})


@app.route("/api/reset-db", methods=["POST"])
def reset_db():
    """
    Clear all client records. Safer than deleting the DB file to avoid Windows locks.
    """
    try:
        conn = get_db()
        conn.execute("DELETE FROM clients")
        conn.commit()
        conn.close()
        return jsonify({"reset": True})
    except Exception as exc:  # pragma: no cover - runtime guard
        return jsonify({"error": f"Could not reset database: {exc}"}), 500


@app.route("/api/export-csv", methods=["GET"])
def export_csv():
    """Generate a CSV of all clients."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM clients ORDER BY created_at DESC").fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    headers = ["ID", "Full Name", "Company", "Email", "Phone", "Status", "Go Factors", "No-Go Factors", "Notes", "Created At"]
    writer.writerow(headers)

    # Write data
    for row in rows:
        writer.writerow([
            row["id"],
            row["full_name"],
            row["company"],
            row["email"],
            row["phone"],
            row["status"],
            row["go_factors"],
            row["no_go_factors"],
            row["notes"],
            row["created_at"]
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=client_signals.csv"}
    )


if __name__ == "__main__":
    # Open the UI automatically for double-click usage.
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    debug_mode = not hasattr(sys, "_MEIPASS")
    app.run(debug=debug_mode, use_reloader=False)
