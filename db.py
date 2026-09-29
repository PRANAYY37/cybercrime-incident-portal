import sqlite3
from pathlib import Path
import pandas as pd
import uuid

DB_PATH = Path(__file__).resolve().parent / "cybercrime.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                reporter_name TEXT NOT NULL,
                contact TEXT,
                incident_date TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                confidence REAL NOT NULL,
                severity TEXT NOT NULL,
                summary TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        conn.commit()


def insert_case(case):
    case_id = "CYB-" + uuid.uuid4().hex[:8].upper()

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO cases (
                case_id,
                created_at,
                reporter_name,
                contact,
                incident_date,
                description,
                category,
                confidence,
                severity,
                summary,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case_id,
            case["created_at"],
            case["reporter_name"],
            case["contact"],
            case["incident_date"],
            case["description"],
            case["category"],
            case["confidence"],
            case["severity"],
            case["summary"],
            case["status"]
        ))

        conn.commit()

    return case_id


def fetch_cases():
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM cases ORDER BY created_at DESC",
            conn
        )


def fetch_case(case_id):
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM cases WHERE case_id = ?",
            (case_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        # Get actual column names
        column_names = [description[0] for description in cursor.description]

        return dict(zip(column_names, row))


def update_case_status(case_id, new_status):
    with get_connection() as conn:
        conn.execute(
            "UPDATE cases SET status = ? WHERE case_id = ?",
            (new_status, case_id)
        )
        conn.commit()


def seed_demo_cases():
    demo_cases = [
        (
            "Demo User",
            "2026-09-20",
            "Received a fake bank SMS asking me to click a verification link and enter an OTP.",
            "Medium"
        ),
        (
            "Demo User",
            "2026-09-21",
            "An unauthorized UPI transaction was reported and money was transferred without permission.",
            "High"
        ),
        (
            "Demo User",
            "2026-09-22",
            "My social media account password was changed and I cannot log in.",
            "High"
        ),
        (
            "Demo User",
            "2026-09-23",
            "Several abusive and threatening messages are being sent repeatedly online.",
            "Medium"
        ),
        (
            "Demo User",
            "2026-09-24",
            "A ransomware program locked files on a computer and displayed a payment demand.",
            "Critical"
        ),
        (
            "Demo User",
            "2026-09-25",
            "A database containing customer records was exposed online.",
            "Critical"
        ),
    ]

    from classifier import classify_incident, generate_summary
    from datetime import datetime

    for reporter, incident_date, description, severity in demo_cases:

        result = classify_incident(description)

        summary = generate_summary(
            description,
            result["category"]
        )

        insert_case({
            "reporter_name": reporter,
            "contact": "demo@example.com",
            "incident_date": incident_date,
            "description": description,
            "category": result["category"],
            "confidence": result["confidence"],
            "severity": severity,
            "summary": summary,
            "status": "New",
            "created_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        })