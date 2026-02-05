import os
import shutil
import tempfile
import unittest
from datetime import datetime

import run


class TestDocumentOrchestrationE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = run.app.test_client()
        cls.test_base_dir = tempfile.mkdtemp(prefix="lexdocs-e2e-", dir="/tmp")
        cls._old_base_dir = run.doc_processor.base_dir
        run.doc_processor.base_dir = cls.test_base_dir

        with run.app.app_context():
            cls.token = run.create_access_token(
                identity=1,
                additional_claims={"rol": "ADMIN", "email": "test@local"},
            )

    @classmethod
    def tearDownClass(cls):
        run.doc_processor.base_dir = cls._old_base_dir
        shutil.rmtree(cls.test_base_dir, ignore_errors=True)

    def _auth_headers(self):
        return {"Cookie": f"access_token_cookie={self.token}"}

    def test_propose_confirm_and_fetch_saved_document(self):
        year = datetime.now().year
        temp_fd, temp_file_path = tempfile.mkstemp(suffix=".pdf", dir="/tmp")
        os.close(temp_fd)
        with open(temp_file_path, "wb") as f:
            f.write(b"%PDF-1.4\n% fake test content")

        extracted_data = {
            "client": "Cliente E2E",
            "doc_type": "demanda",
            "date": f"{year}-02-05",
            "expedient": "E2E/2026/001",
            "court": "Juzgado de Prueba",
            "year": year,
            "confidence": 99,
        }

        propose_resp = self.client.post(
            "/api/document/propose-save",
            json={"temp_file_path": temp_file_path, "extracted_data": extracted_data},
            headers=self._auth_headers(),
        )
        self.assertEqual(propose_resp.status_code, 200, propose_resp.get_data(as_text=True))
        propose_data = propose_resp.get_json()
        self.assertTrue(propose_data.get("success"))
        self.assertIsNotNone(propose_data.get("pending_document_id"))

        confirmed_data = propose_data["proposal"]
        confirm_resp = self.client.post(
            "/api/document/confirm-save",
            json={
                "pending_document_id": propose_data["pending_document_id"],
                "confirmed_data": confirmed_data,
            },
            headers=self._auth_headers(),
        )
        self.assertEqual(confirm_resp.status_code, 200, confirm_resp.get_data(as_text=True))
        confirm_data = confirm_resp.get_json()
        self.assertTrue(confirm_data.get("success"))
        self.assertIsNotNone(confirm_data.get("document_id"))
        self.assertTrue(os.path.exists(confirm_data["final_path"]))
        self.assertFalse(os.path.exists(temp_file_path))

        saved_id = confirm_data["document_id"]
        detail_resp = self.client.get(
            f"/api/document/saved/{saved_id}",
            headers=self._auth_headers(),
        )
        self.assertEqual(detail_resp.status_code, 200, detail_resp.get_data(as_text=True))
        detail_data = detail_resp.get_json()
        self.assertTrue(detail_data.get("success"))
        self.assertEqual(detail_data["document"]["id"], saved_id)

        list_resp = self.client.get("/api/document/saved?limit=10", headers=self._auth_headers())
        self.assertEqual(list_resp.status_code, 200, list_resp.get_data(as_text=True))
        list_data = list_resp.get_json()
        self.assertTrue(list_data.get("success"))
        self.assertTrue(any(d["id"] == saved_id for d in list_data.get("documents", [])))


if __name__ == "__main__":
    unittest.main()
