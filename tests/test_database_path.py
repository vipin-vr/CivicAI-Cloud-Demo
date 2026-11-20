from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import database


class DatabasePathConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH

    def tearDown(self) -> None:
        database.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_default_path_is_preserved_when_not_configured(self) -> None:
        self.assertEqual(database.resolve_database_path({}), database.DEFAULT_DB_PATH)
        self.assertEqual(database.DB_PATH, database.DEFAULT_DB_PATH)

    def test_configured_absolute_path_creates_parent_and_supports_operations(self) -> None:
        configured_path = Path(self.temp_dir.name) / "private-data" / "civicai-production.db"
        resolved = database.resolve_database_path({"CIVICAI_DB_PATH": str(configured_path)})
        self.assertEqual(resolved, configured_path.resolve())
        self.assertFalse(configured_path.parent.exists())
        database.DB_PATH = resolved
        database.initialize_database()
        self.assertTrue(configured_path.exists())
        self.assertEqual(database.dashboard_counts()["Total"], 0)

    def test_relative_project_cloud_and_static_paths_are_rejected(self) -> None:
        with self.assertRaises(database.DatabasePathError):
            database.resolve_database_path({"CIVICAI_DB_PATH": "relative.db"})
        with self.assertRaises(database.DatabasePathError):
            database.resolve_database_path({"CIVICAI_DB_PATH": str(database.PROJECT_ROOT / "private.db")})
        with self.assertRaises(database.DatabasePathError):
            database.resolve_database_path({"CIVICAI_DB_PATH": str(database.PROJECT_ROOT / "static" / "private.db")})
        cloud_path = Path(self.temp_dir.name) / "OneDrive" / "civicai.db"
        with self.assertRaises(database.DatabasePathError):
            database.resolve_database_path({"CIVICAI_DB_PATH": str(cloud_path)})
        configured_cloud_path = Path(self.temp_dir.name) / "cloud-root"
        with self.assertRaises(database.DatabasePathError):
            database.resolve_database_path({"CIVICAI_DB_PATH": str(configured_cloud_path / "civicai.db"), "Dropbox": str(configured_cloud_path)})


if __name__ == "__main__":
    unittest.main()
