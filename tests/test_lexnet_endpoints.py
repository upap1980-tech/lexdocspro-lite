import unittest
from pathlib import Path
from unittest.mock import patch
import tempfile
from datetime import datetime, timedelta

import run
from services.lexnet_notifications import LexNetNotifications


class TestLexNetEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = run.app.test_client()
        cls.created_notification_ids = []
        cls.fixture_dir = Path(__file__).parent / "fixtures"
        cls.auth_headers = {}
        if getattr(run, "JWT_EXTENSION_AVAILABLE", False):
            with run.app.app_context():
                token = run.create_access_token(
                    identity=1,
                    additional_claims={"rol": "ADMIN", "email": "test@local"},
                )
            cls.auth_headers = {"Cookie": f"access_token_cookie={token}"}

    @classmethod
    def tearDownClass(cls):
        if not cls.created_notification_ids:
            return
        conn = run.db.get_connection()
        try:
            cur = conn.cursor()
            for nid in cls.created_notification_ids:
                cur.execute("DELETE FROM notifications WHERE id = ?", (nid,))
            conn.commit()
        finally:
            conn.close()

    def _create_notification_from_xml(self):
        xml_path = self.fixture_dir / "lexnet_notification.xml"
        with xml_path.open("rb") as f:
            response = self.client.post(
                "/api/lexnet/upload-notification",
                data={"file": (f, "lexnet_notification.xml")},
                content_type="multipart/form-data",
                headers=self.auth_headers,
            )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertTrue(payload.get("success"))
        nid = payload["notification_id"]
        self.created_notification_ids.append(nid)
        return nid

    def _insert_notification(self, title, urgency="NORMAL", read=0, archived=0):
        # Garantiza migración de esquema antes de inserts directos para tests.
        LexNetNotifications(db_manager=run.db)
        conn = run.db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO notifications
                (user_id, type, title, body, deadline, urgency, procedure_number, court, read, archived, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    None,
                    "lexnet",
                    title,
                    "body-test",
                    None,
                    urgency,
                    "TEST/2026",
                    "Juzgado Test",
                    int(read),
                    int(archived),
                ),
            )
            conn.commit()
            nid = cur.lastrowid
        finally:
            conn.close()
        self.created_notification_ids.append(nid)
        return nid

    def _insert_notification_advanced(
        self,
        title,
        urgency="NORMAL",
        read=0,
        archived=0,
        case_type=None,
        procedure_number="TEST/2026",
        created_at=None,
    ):
        LexNetNotifications(db_manager=run.db)
        conn = run.db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO notifications
                (
                    user_id, type, title, body, deadline, urgency, procedure_number, court,
                    notification_date, deadline_days, case_type, resolution_type, parties_json,
                    read, archived, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    None,
                    "lexnet",
                    title,
                    "body-test-adv",
                    None,
                    urgency,
                    procedure_number,
                    "Juzgado Test",
                    None,
                    None,
                    case_type,
                    None,
                    "{}",
                    int(read),
                    int(archived),
                    created_at or datetime.now().isoformat(),
                ),
            )
            conn.commit()
            nid = cur.lastrowid
        finally:
            conn.close()
        self.created_notification_ids.append(nid)
        return nid

    def test_upload_notification_xml_and_query_endpoints(self):
        created_id = self._create_notification_from_xml()
        self.assertIsNotNone(created_id)

        list_response = self.client.get(
            "/api/lexnet/notifications?unread=true&limit=20",
            headers=self.auth_headers,
        )
        self.assertEqual(list_response.status_code, 200, list_response.get_data(as_text=True))
        list_data = list_response.get_json()
        self.assertTrue(list_data.get("success"))
        self.assertIsInstance(list_data.get("notifications"), list)

        urgent_response = self.client.get("/api/lexnet/urgent-count", headers=self.auth_headers)
        self.assertEqual(urgent_response.status_code, 200, urgent_response.get_data(as_text=True))
        urgent_data = urgent_response.get_json()
        self.assertTrue(urgent_data.get("success"))
        self.assertIsInstance(urgent_data.get("urgent_count"), int)

    def test_upload_notification_pdf_controlled(self):
        pdf_path = self.fixture_dir / "lexnet_notification.pdf"
        fake_pdf_text = (
            "JUZGADO DE LO PENAL Nº 3. Procedimiento 777/2026. "
            "Fecha notificación: 04/02/2026. Plazo de 5 días."
        )
        with patch(
            "services.lexnet_notifications.LexNetNotifications._extract_text_from_pdf",
            return_value=fake_pdf_text,
        ):
            with pdf_path.open("rb") as f:
                response = self.client.post(
                    "/api/lexnet/upload-notification",
                    data={"file": (f, "lexnet_notification.pdf")},
                    content_type="multipart/form-data",
                    headers=self.auth_headers,
                )

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertTrue(payload.get("success"))
        self.assertIn("notification_id", payload)
        self.created_notification_ids.append(payload["notification_id"])

    def test_mark_notification_as_read_endpoint(self):
        notification_id = self._create_notification_from_xml()
        read_endpoint = f"/api/lexnet/notifications/{notification_id}/read"
        response = self.client.patch(read_endpoint, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertTrue(payload.get("success"))

        conn = run.db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT read FROM notifications WHERE id = ?", (notification_id,))
            row = cur.fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 1)

    def test_lexnet_analyze_endpoint_controlled(self):
        expected_analysis = "ANALISIS CONTROLADO TEST"
        with tempfile.TemporaryDirectory(prefix="lexnet-analyze-", dir="/tmp") as temp_output_dir:
            with patch.object(run, "GENERATED_DOCS_DIR", temp_output_dir):
                with patch.object(run.lexnet_analyzer, "analizar_notificacion", return_value=expected_analysis):
                    response = self.client.post(
                        "/api/lexnet/analyze",
                        json={
                            "textos": {"principal": "Texto notificación"},
                            "provider": "ollama",
                            "archivos": ["lexnet_notification.xml"],
                            "nombre": "Caso Test",
                        },
                        headers=self.auth_headers,
                    )

        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertTrue(payload.get("success"))
        self.assertEqual(payload.get("analisis"), expected_analysis)
        self.assertTrue(payload.get("filename", "").startswith("ANALISIS_LEXNET_"))
        self.assertTrue(payload.get("filepath", "").endswith(".txt"))

        generated_file = payload.get("filepath")
        if generated_file and Path(generated_file).exists():
            Path(generated_file).unlink()

    def test_notifications_filters_urgency_and_unread_combined(self):
        base = "UT-FILTER-LEXNET"
        unread_urgent_id = self._insert_notification(f"{base}-A", urgency="URGENT", read=0)
        _read_urgent_id = self._insert_notification(f"{base}-B", urgency="URGENT", read=1)
        _unread_normal_id = self._insert_notification(f"{base}-C", urgency="NORMAL", read=0)
        _archived_urgent_id = self._insert_notification(f"{base}-D", urgency="URGENT", read=0, archived=1)

        response = self.client.get(
            "/api/lexnet/notifications?unread=true&urgency=URGENT&limit=100",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertTrue(payload.get("success"))
        notifications = payload.get("notifications", [])
        ids = {n.get("id") for n in notifications}

        self.assertIn(unread_urgent_id, ids)
        # Validación funcional fuerte: cada item debe respetar ambos filtros.
        for item in notifications:
            self.assertEqual(item.get("urgency"), "URGENT")
            self.assertEqual(item.get("read"), 0)
            self.assertEqual(item.get("archived"), 0)

    def test_notifications_filters_case_type_date_and_procedure(self):
        now = datetime.now()
        target_day = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        target_dt = f"{target_day}T12:00:00"

        matched_id = self._insert_notification_advanced(
            title="UT-ADV-FILTER-A",
            urgency="URGENT",
            case_type="JUICIO_VERBAL",
            procedure_number="PROC-ABC-2026",
            created_at=target_dt,
            read=0,
        )
        _wrong_case_id = self._insert_notification_advanced(
            title="UT-ADV-FILTER-B",
            urgency="URGENT",
            case_type="EJECUCION",
            procedure_number="PROC-ABC-2026",
            created_at=target_dt,
            read=0,
        )
        _wrong_proc_id = self._insert_notification_advanced(
            title="UT-ADV-FILTER-C",
            urgency="URGENT",
            case_type="JUICIO_VERBAL",
            procedure_number="PROC-OTHER-2026",
            created_at=target_dt,
            read=0,
        )

        endpoint = (
            "/api/lexnet/notifications"
            f"?unread=true&urgency=URGENT&case_type=JUICIO_VERBAL"
            f"&procedure_number=ABC&date_from={target_day}&date_to={target_day}&limit=100"
        )
        response = self.client.get(endpoint, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertTrue(payload.get("success"))
        notifications = payload.get("notifications", [])
        ids = {n.get("id") for n in notifications}
        self.assertIn(matched_id, ids)
        for item in notifications:
            self.assertEqual(item.get("urgency"), "URGENT")
            self.assertEqual(item.get("read"), 0)
            self.assertEqual(item.get("case_type"), "JUICIO_VERBAL")
            self.assertIn("ABC", item.get("procedure_number", ""))

    def test_notifications_retro_compatibility_without_advanced_fields(self):
        legacy_id = self._insert_notification(
            title="UT-RETRO-LEGACY",
            urgency="NORMAL",
            read=0,
            archived=0,
        )
        response = self.client.get(
            "/api/lexnet/notifications?limit=100",
            headers=self.auth_headers,
        )
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        payload = response.get_json()
        self.assertTrue(payload.get("success"))
        by_id = {n.get("id"): n for n in payload.get("notifications", [])}
        self.assertIn(legacy_id, by_id)
        legacy_item = by_id[legacy_id]
        self.assertIn("parties", legacy_item)
        self.assertIsInstance(legacy_item.get("parties"), dict)


if __name__ == "__main__":
    unittest.main()
