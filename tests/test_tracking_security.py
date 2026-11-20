from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import database


class TrackingSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "tracking-test.db"
        self.original_db_path = database.DB_PATH
        database.DB_PATH = self.db_path

    def tearDown(self) -> None:
        database.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def record(self, complaint_id: str, token_hash: str | None) -> dict[str, object]:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "complaint_id": complaint_id, "citizen_name": "Test Citizen", "category": "Water Leakage",
            "description": "Water is leaking near the bus stop.", "location": "Test Location",
            "image_path": None, "ai_analysis": "{}", "severity": "Medium", "public_risk": 50,
            "public_impact": 50, "priority_score": 50, "priority_label": "Medium",
            "suggested_department": "Water Supply Department", "ai_category": "Water Leakage",
            "ai_generated_description": "Water is leaking near the bus stop.",
            "ai_suggested_department": "Water Supply Department", "mismatch_flag": 0,
            "duplicate_flag": 0, "tracking_token_hash": token_hash, "status": "Submitted",
            "created_at": now, "updated_at": now,
        }

    def test_additive_migration_preserves_legacy_record(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("CREATE TABLE complaints (id INTEGER PRIMARY KEY AUTOINCREMENT, complaint_id TEXT NOT NULL UNIQUE, citizen_name TEXT NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL, location TEXT NOT NULL, image_path TEXT, ai_analysis TEXT, severity TEXT NOT NULL, public_risk INTEGER NOT NULL, public_impact INTEGER NOT NULL, priority_score REAL NOT NULL, priority_label TEXT NOT NULL, suggested_department TEXT, duplicate_flag INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'Submitted', created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
            conn.execute("INSERT INTO complaints (complaint_id, citizen_name, category, description, location, severity, public_risk, public_impact, priority_score, priority_label, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ("LEGACY-1", "Legacy", "Water Leakage", "Existing record", "Old location", "Medium", 50, 50, 50, "Medium", "2026-01-01", "2026-01-01"))
            conn.commit()
        finally:
            conn.close()
        database.initialize_database()
        self.assertIsNone(database.get_complaint("LEGACY-1")["tracking_token_hash"])
        self.assertIsNone(database.get_complaint("LEGACY-1")["duplicate_complaint_id"])
        self.assertEqual(database.get_complaint("LEGACY-1")["description"], "Existing record")

    def test_tracking_token_verification_and_admin_regression(self) -> None:
        database.initialize_database()
        token = database.generate_tracking_token()
        complaint_id = "TOKEN-VALID"
        database.create_complaint(self.record(complaint_id, database.hash_tracking_token(token)))
        saved = database.get_complaint(complaint_id)
        self.assertNotEqual(saved["tracking_token_hash"], token)
        self.assertEqual(saved["tracking_token_hash"], database.hash_tracking_token(token))
        self.assertNotIn(token, " ".join(str(value) for value in saved.values() if value is not None))
        self.assertIsNone(database.get_complaint_for_tracking(complaint_id, ""))
        self.assertIsNone(database.get_complaint_for_tracking(complaint_id, "incorrect-token"))
        self.assertEqual(database.get_complaint_for_tracking(complaint_id, token)["description"], self.record(complaint_id, None)["description"])
        database.create_complaint(self.record("TOKEN-LEGACY", None))
        self.assertIsNone(database.get_complaint_for_tracking("TOKEN-LEGACY", token))
        self.assertTrue(database.update_complaint_review(complaint_id, "Water Leakage", "Water Supply Department"))
        self.assertTrue(database.update_complaint_status(complaint_id, "Resolved"))
        admin_record = database.get_complaint(complaint_id)
        self.assertEqual(admin_record["status"], "Resolved")
        self.assertEqual(admin_record["reviewed_flag"], 1)


if __name__ == "__main__":
    unittest.main()
