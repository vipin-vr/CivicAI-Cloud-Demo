from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from argon2 import PasswordHasher

import admin_auth
import database


class AdminAuthenticationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH
        database.DB_PATH = Path(self.temp_dir.name) / "admin-auth-test.db"
        database.initialize_database()
        self.password = "generated-test-password-not-used-anywhere-else"
        self.password_hash = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(self.password)
        self.environment = {"ADMIN_USERNAME": "civicai_ops", "ADMIN_PASSWORD_HASH": self.password_hash}
        self.client = "test-client-identifier"
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        database.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_configuration_rejects_missing_malformed_placeholder_default_and_plaintext(self) -> None:
        self.assertFalse(admin_auth.validate_admin_configuration({}))
        self.assertFalse(admin_auth.validate_admin_configuration({"ADMIN_USERNAME": "civicai_ops", "ADMIN_PASSWORD_HASH": "not-a-hash"}))
        self.assertFalse(admin_auth.validate_admin_configuration({"ADMIN_USERNAME": "admin", "ADMIN_PASSWORD_HASH": self.password_hash}))
        self.assertFalse(admin_auth.validate_admin_configuration({"ADMIN_USERNAME": "<unique_admin_username>", "ADMIN_PASSWORD_HASH": self.password_hash}))
        self.assertFalse(admin_auth.validate_admin_configuration({"ADMIN_USERNAME": "civicai_ops", "ADMIN_PASSWORD_HASH": self.password_hash, "ADMIN_PASSWORD": "plaintext-not-accepted"}))
        self.assertTrue(admin_auth.validate_admin_configuration(self.environment))

    def test_short_password_cannot_authenticate_even_if_its_hash_is_configured(self) -> None:
        short_password = "too-short"
        short_environment = {
            "ADMIN_USERNAME": "civicai_ops",
            "ADMIN_PASSWORD_HASH": PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(short_password),
        }
        result = admin_auth.authenticate_admin("civicai_ops", short_password, self.client, short_environment, self.now)
        self.assertFalse(result.authenticated)

    def test_proxy_client_identifier_never_accepts_forwarded_headers(self) -> None:
        proxy_environment = {
            **self.environment,
            "ADMIN_TRUSTED_CLIENT_ID_HEADER": "X-CivicAI-Client-ID",
            "ADMIN_TRUSTED_PROXY_AUTH_HEADER": "X-CivicAI-Proxy-Auth",
            "ADMIN_TRUSTED_PROXY_AUTH_VALUE": "test-proxy-auth-value",
        }
        verified = admin_auth.resolve_client_identifier(
            {"X-CivicAI-Client-ID": "proxy-client", "X-CivicAI-Proxy-Auth": "test-proxy-auth-value"}, "session-client", proxy_environment
        )
        self.assertTrue(verified.proxy_verified)
        self.assertEqual(verified.value, "proxy-client")
        forwarded_only = admin_auth.resolve_client_identifier({"X-Forwarded-For": "203.0.113.5"}, "session-client", proxy_environment)
        self.assertFalse(forwarded_only.proxy_verified)
        self.assertEqual(forwarded_only.value, "session-client")
        forwarded_config = {**proxy_environment, "ADMIN_TRUSTED_CLIENT_ID_HEADER": "X-Forwarded-For"}
        rejected = admin_auth.resolve_client_identifier({"X-Forwarded-For": "203.0.113.5", "X-CivicAI-Proxy-Auth": "test-proxy-auth-value"}, "session-client", forwarded_config)
        self.assertFalse(rejected.proxy_verified)

    def test_valid_login_clears_failures_and_admin_database_functions_remain_available(self) -> None:
        admin_auth.authenticate_admin("civicai_ops", "wrong-password", self.client, self.environment, self.now)
        result = admin_auth.authenticate_admin("civicai_ops", self.password, self.client, self.environment, self.now)
        self.assertTrue(result.authenticated)
        with database.connection() as conn:
            self.assertIsNone(conn.execute("SELECT 1 FROM admin_login_attempts WHERE identifier_hash = ?", (admin_auth.hash_client_identifier(self.client),)).fetchone())
        self.assertFalse(database.update_complaint_status("missing", "invalid"))

    def test_five_failures_lock_and_correct_credentials_cannot_bypass_lock(self) -> None:
        for _ in range(4):
            result = admin_auth.authenticate_admin("civicai_ops", "wrong-password", self.client, self.environment, self.now)
            self.assertFalse(result.locked)
        fifth = admin_auth.authenticate_admin("civicai_ops", "wrong-password", self.client, self.environment, self.now)
        self.assertTrue(fifth.locked)
        blocked_correct = admin_auth.authenticate_admin("civicai_ops", self.password, self.client, self.environment, self.now)
        self.assertFalse(blocked_correct.authenticated)
        self.assertTrue(blocked_correct.locked)
        after_expiry = admin_auth.authenticate_admin("civicai_ops", self.password, self.client, self.environment, self.now + timedelta(minutes=15, seconds=1))
        self.assertTrue(after_expiry.authenticated)

    def test_failure_window_expiry_and_redacted_logging(self) -> None:
        with self.assertLogs("admin_auth", level="WARNING") as captured:
            admin_auth.authenticate_admin("civicai_ops", self.password + "-wrong", self.client, self.environment, self.now)
        log_output = "\n".join(captured.output)
        self.assertNotIn(self.password, log_output)
        self.assertNotIn(self.password_hash, log_output)
        self.assertNotIn(self.client, log_output)
        later = self.now + timedelta(minutes=16)
        admin_auth.authenticate_admin("civicai_ops", "wrong-password", self.client, self.environment, later)
        with database.connection() as conn:
            row = conn.execute("SELECT failed_count FROM admin_login_attempts WHERE identifier_hash = ?", (admin_auth.hash_client_identifier(self.client),)).fetchone()
        self.assertEqual(row["failed_count"], 1)

    def test_only_hashed_client_identifiers_are_stored(self) -> None:
        admin_auth.authenticate_admin("civicai_ops", "wrong-password", self.client, self.environment, self.now)
        conn = sqlite3.connect(database.DB_PATH)
        try:
            row = conn.execute("SELECT identifier_hash FROM admin_login_attempts").fetchone()
        finally:
            conn.close()
        self.assertEqual(row[0], admin_auth.hash_client_identifier(self.client))
        self.assertNotEqual(row[0], self.client)


if __name__ == "__main__":
    unittest.main()
