import unittest

import run


class TestBusinessSkills(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = run.app.test_client()
        cls.auth_headers = {}
        if getattr(run, "JWT_EXTENSION_AVAILABLE", False):
            with run.app.app_context():
                token = run.create_access_token(
                    identity=1,
                    additional_claims={"rol": "ADMIN", "email": "test@local"},
                )
            cls.auth_headers = {"Cookie": f"access_token_cookie={token}"}

    def test_jurisdictions_endpoint(self):
        r = self.client.get("/api/business/jurisdictions")
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        data = r.get_json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("jurisdictions"), list)
        self.assertTrue(any(j.get("id") == "ES_CANARIAS" for j in data["jurisdictions"]))

    def test_templates_by_jurisdiction(self):
        r = self.client.get("/api/business/templates?jurisdiction=ES_CANARIAS")
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        data = r.get_json()
        self.assertTrue(data.get("success"))
        templates = data.get("templates", [])
        self.assertTrue(any(t.get("doc_type") == "lexnet_urgente" for t in templates))

    def test_strategy_endpoint_with_deadline(self):
        payload = {
            "query": "Preparar oposición a demanda",
            "jurisdiction": "ES_GENERAL",
            "doc_type": "demanda",
            "fecha_notificacion": "2026-02-04",
            "plazo_dias": 20,
        }
        r = self.client.post("/api/business/strategy", json=payload, headers=self.auth_headers)
        self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
        data = r.get_json()
        self.assertTrue(data.get("success"))
        strategy = data.get("strategy", {})
        self.assertEqual(strategy.get("jurisdiction"), "ES_GENERAL")
        self.assertEqual(strategy.get("doc_type"), "demanda")
        self.assertIn("styled_prompt", strategy)
        self.assertIsInstance(strategy.get("recommended_steps"), list)
        self.assertIsNotNone(strategy.get("deadline"))


if __name__ == "__main__":
    unittest.main()
