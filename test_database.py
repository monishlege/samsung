import sqlite3
import tempfile
import unittest
from contextlib import closing
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import database
from PIL import Image


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "campus.db"
        self.original_database_path = database.DB_NAME
        database.DB_NAME = str(self.database_path)
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.execute("""
                CREATE TABLE complaints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    complaint TEXT,
                    category TEXT,
                    priority TEXT,
                    status TEXT DEFAULT 'Pending'
                )
            """)
            connection.execute(
                """
                INSERT INTO complaints (name, complaint, category, priority)
                VALUES ('Legacy user', 'Old issue', 'General', 'Low')
                """
            )
            connection.commit()
        database.create_table()

    def tearDown(self):
        database.DB_NAME = self.original_database_path
        self.temp_dir.cleanup()

    def test_passwords_are_hashed_and_sign_in_is_verified(self):
        password = "a-long-and-unique-test-password"
        user_id = database.create_user(
            "Test Student",
            "test.student",
            password,
            "Student",
        )

        with closing(sqlite3.connect(self.database_path)) as connection:
            stored_hash = connection.execute(
                "SELECT password_hash FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()[0]

        self.assertNotEqual(stored_hash, password)
        self.assertTrue(database.verify_password(password, stored_hash))
        self.assertFalse(database.verify_password("wrong-password", stored_hash))
        self.assertEqual(
            database.authenticate_user("TEST.STUDENT", password)["id"],
            user_id,
        )
        self.assertIsNone(
            database.authenticate_user("test.student", "wrong-password")
        )

    def test_self_registration_cannot_assign_privileged_roles(self):
        with self.assertRaises(ValueError):
            database.create_user(
                "Unauthorized Admin",
                "not-admin",
                "a-long-and-unique-test-password",
                "Admin",
            )

    def test_failed_sign_ins_temporarily_lock_the_username(self):
        database.create_user(
            "Test Student",
            "test.student",
            "a-long-and-unique-test-password",
            "Student",
        )
        with patch("database.time.time", return_value=1_000):
            for _ in range(database.MAX_LOGIN_FAILURES):
                self.assertIsNone(
                    database.authenticate_user("test.student", "wrong-password")
                )
            self.assertIsNone(
                database.authenticate_user(
                    "test.student",
                    "a-long-and-unique-test-password",
                )
            )

        with patch(
            "database.time.time",
            return_value=1_000 + database.LOGIN_LOCK_SECONDS + 1,
        ):
            self.assertIsNotNone(
                database.authenticate_user(
                    "test.student",
                    "a-long-and-unique-test-password",
                )
            )

    def test_complaints_are_scoped_to_the_owner(self):
        first_user_id = database.create_user(
            "First Student",
            "first.student",
            "a-long-and-unique-test-password",
            "Student",
        )
        second_user_id = database.create_user(
            "Second Student",
            "second.student",
            "another-long-unique-test-password",
            "Student",
        )
        database.add_complaint(
            first_user_id,
            "First Student",
            "Broken fan",
            "Electrical",
            "Medium",
        )

        first_complaints = database.get_complaints(first_user_id)
        second_complaints = database.get_complaints(second_user_id)
        all_complaints = database.get_complaints()

        self.assertEqual(first_complaints["complaint"].tolist(), ["Broken fan"])
        self.assertTrue(second_complaints.empty)
        self.assertEqual(len(all_complaints), 2)

    def test_existing_complaints_are_preserved_by_schema_migration(self):
        with closing(sqlite3.connect(self.database_path)) as connection:
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(complaints)")
            }
            legacy_complaint = connection.execute(
                "SELECT complaint, user_id FROM complaints WHERE id = 1"
            ).fetchone()

        self.assertIn("user_id", columns)
        self.assertIn("resolution_image", columns)
        self.assertIn("resolution_latitude", columns)
        self.assertIn("resolution_longitude", columns)
        self.assertEqual(legacy_complaint, ("Old issue", None))

    def test_only_ai_confirmed_maintenance_submission_can_resolve(self):
        database.create_bootstrap_admin(
            "campusadmin",
            "a-unique-bootstrap-password",
        )
        admin_id = database.authenticate_user(
            "campusadmin",
            "a-unique-bootstrap-password",
        )["id"]
        owner_id = database.create_user(
            "Complaint Owner",
            "complaint.owner",
            "a-long-and-unique-test-password",
            "Student",
        )
        staff_id = database.create_user(
            "Maintenance Worker",
            "maintenance.worker",
            "another-long-unique-test-password",
            "Student",
        )
        database.update_user_role(admin_id, staff_id, "Maintenance Staff")
        database.add_complaint(
            owner_id,
            "Complaint Owner",
            "Broken classroom fan",
            "Electrical",
            "Medium",
        )
        complaint_id = int(database.get_complaints(owner_id).iloc[0]["id"])

        image_buffer = BytesIO()
        Image.new("RGB", (2, 2), "green").save(image_buffer, format="PNG")
        image_bytes = image_buffer.getvalue()

        with self.assertRaises(PermissionError):
            database.submit_resolution(
                owner_id,
                complaint_id,
                "The fan works now.",
                image_bytes,
                12.9716,
                77.5946,
                8.0,
            )
        with self.assertRaises(ValueError):
            database.submit_resolution(
                staff_id,
                complaint_id,
                "The fan works now.",
                image_bytes,
                91,
                77.5946,
                8.0,
            )
        with self.assertRaises(ValueError):
            database.submit_resolution(
                staff_id,
                complaint_id,
                "The fan works now.",
                b"not an image",
                12.9716,
                77.5946,
                8.0,
            )

        rejected = database.submit_resolution(
            staff_id,
            complaint_id,
            "Repaired the fan, but it is still not working.",
            image_bytes,
            12.9716,
            77.5946,
            8.0,
        )
        self.assertFalse(rejected["confirmed"])
        self.assertEqual(rejected["status"], "In Progress")
        self.assertEqual(
            database.get_complaints(owner_id).iloc[0]["status"],
            "In Progress",
        )

        with closing(sqlite3.connect(self.database_path)) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "UPDATE complaints SET status = 'Resolved' WHERE id = ?",
                    (complaint_id,),
                )

        approved = database.submit_resolution(
            staff_id,
            complaint_id,
            "Repaired the fan; it works now.",
            image_bytes,
            12.9716,
            77.5946,
            8.0,
        )
        self.assertTrue(approved["confirmed"])
        self.assertEqual(approved["status"], "Resolved")

        complaints = database.get_complaints(owner_id)
        self.assertEqual(complaints.iloc[0]["status"], "Resolved")
        evidence = database.get_complaint_resolution(owner_id, complaint_id)
        self.assertEqual(evidence["image"], image_bytes)
        self.assertEqual(evidence["latitude"], 12.9716)
        self.assertEqual(evidence["longitude"], 77.5946)
        self.assertEqual(evidence["resolved_by"], staff_id)
        self.assertTrue(evidence["ai_confirmed"])
        self.assertEqual(evidence["notes"], "Repaired the fan; it works now.")
        self.assertTrue(evidence["ai_feedback"])

        other_user_id = database.create_user(
            "Other Student",
            "other.student",
            "a-third-long-and-unique-test-password",
            "Student",
        )
        with self.assertRaises(PermissionError):
            database.get_complaint_resolution(other_user_id, complaint_id)

    def test_bootstrap_admin_and_last_admin_protection(self):
        self.assertTrue(
            database.create_bootstrap_admin(
                "campusadmin",
                "a-unique-bootstrap-password",
            )
        )
        self.assertFalse(
            database.create_bootstrap_admin(
                "campusadmin",
                "a-unique-bootstrap-password",
            )
        )
        admin_id = database.authenticate_user(
            "campusadmin",
            "a-unique-bootstrap-password",
        )["id"]
        student_id = database.create_user(
            "Test Student",
            "test.student",
            "a-long-and-unique-test-password",
            "Student",
        )

        with self.assertRaises(ValueError):
            database.update_user_role(admin_id, admin_id, "Student")
        with self.assertRaises(PermissionError):
            database.update_user_role(student_id, admin_id, "Faculty")


if __name__ == "__main__":
    unittest.main()
