from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import database
from duplicate_detection import find_possible_duplicate


class DuplicateDetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH
        database.DB_PATH = Path(self.temp_dir.name) / "duplicate-test.db"
        database.initialize_database()

    def tearDown(self) -> None:
        database.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_matching_complaint_id_is_returned_and_can_be_persisted(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        database.create_complaint({
            "complaint_id": "CIV-EXISTING", "citizen_name": "Citizen", "category": "Water Leakage",
            "description": "Water leaking beside the central bus stop", "location": "Central Bus Stop",
            "image_path": None, "ai_analysis": "{}", "severity": "Medium", "public_risk": 50,
            "public_impact": 50, "priority_score": 50, "priority_label": "High",
            "suggested_department": "Water Supply Department", "duplicate_flag": 0,
            "duplicate_complaint_id": None, "status": "Submitted", "created_at": now, "updated_at": now,
        })
        duplicate, complaint_id = find_possible_duplicate(
            "Water Leakage", "Central Bus Stop", "Water leaking next to the central bus stop"
        )
        self.assertTrue(duplicate)
        self.assertEqual(complaint_id, "CIV-EXISTING")
        database.create_complaint({
            "complaint_id": "CIV-NEW", "citizen_name": "Citizen", "category": "Water Leakage",
            "description": "Water leaking next to the central bus stop", "location": "Central Bus Stop",
            "image_path": None, "ai_analysis": "{}", "severity": "Medium", "public_risk": 50,
            "public_impact": 50, "priority_score": 50, "priority_label": "High",
            "suggested_department": "Water Supply Department", "duplicate_flag": int(duplicate),
            "duplicate_complaint_id": complaint_id, "status": "Submitted", "created_at": now, "updated_at": now,
        })
        self.assertEqual(database.get_complaint("CIV-NEW")["duplicate_complaint_id"], "CIV-EXISTING")

    def test_different_location_is_not_a_duplicate(self) -> None:
        self.assertEqual(find_possible_duplicate("Water Leakage", "Other location", "Water leak"), (False, None))
