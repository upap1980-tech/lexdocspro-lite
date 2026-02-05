import os
import unittest
from unittest.mock import patch

import run
from services.ia_cascade_service import IACascadeService


class TestIACascadeEnterprise(unittest.TestCase):
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

    def test_anthropic_alias_is_loaded_for_claude(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "anthropic-test-key"}, clear=False):
            svc = IACascadeService()
        cfg = svc.get_provider_config("claude")
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg.get("api_key"), "anthropic-test-key")
        self.assertTrue(cfg.get("enabled"))

    def test_empty_prompt_is_rejected(self):
        svc = IACascadeService()
        result = svc.consultar_cascade("   ", temperature=0.2, max_tokens=200)
        self.assertFalse(result.get("success"))
        self.assertIn("Prompt vacío", result.get("error", ""))

    def test_cannot_disable_last_enabled_provider(self):
        svc = IACascadeService()
        # Fuerza todos deshabilitados salvo ollama para validar guard-rail.
        for pid in svc.providers_config:
            svc.providers_config[pid]["enabled"] = False
        svc.providers_config["ollama"]["enabled"] = True
        ok = svc.toggle_provider("ollama", False)
        self.assertFalse(ok)
        self.assertTrue(svc.providers_config["ollama"]["enabled"])

    def test_successful_call_updates_tokens_used(self):
        svc = IACascadeService()
        with patch.object(
            svc,
            "_call_ollama",
            return_value={"success": True, "response": "ok", "metadata": {"tokens": 15}},
        ):
            res = svc.consultar_cascade("test tokens", force_provider="ollama")
        self.assertTrue(res.get("success"))
        stats = svc.get_stats()
        self.assertGreaterEqual(stats["providers"]["ollama"]["tokens_used"], 15)

    def test_health_endpoint_non_500(self):
        resp = self.client.get("/api/ia-cascade/health", headers=self.auth_headers)
        self.assertLess(resp.status_code, 500)

    def test_stats_public_endpoints_are_stable(self):
        resp1 = self.client.get("/api/ia-cascade/stats-public", headers=self.auth_headers)
        resp2 = self.client.get("/api/ia-cascade/providers-public", headers=self.auth_headers)
        self.assertIn(resp1.status_code, (200, 401, 403))
        self.assertIn(resp2.status_code, (200, 401, 403))

    def test_audit_persistence_for_test_call(self):
        if run.ia_cascade is None:
            self.skipTest("ia_cascade no disponible")
        request_id = "ut-req-ia-cascade"
        correlation_id = "ut-corr-ia-cascade"
        mocked_result = {
            "success": True,
            "response": "ok",
            "provider_used": "ollama",
            "time": 0.12,
            "metadata": {"model": "mock-model", "tokens": 7},
            "error": None,
        }
        with patch.object(run.ia_cascade, "consultar_cascade", return_value=mocked_result):
            resp = self.client.post(
                "/api/ia-cascade/test",
                json={"prompt": "test audit", "provider": "cascade"},
                headers={
                    **self.auth_headers,
                    "X-Request-ID": request_id,
                    "X-Correlation-ID": correlation_id,
                },
            )

        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        payload = resp.get_json()
        self.assertEqual(payload.get("request_id"), request_id)
        self.assertEqual(payload.get("correlation_id"), correlation_id)
        self.assertTrue(payload.get("success"))

        conn = run.db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT request_id, correlation_id, endpoint, provider_used, success
                FROM ia_cascade_audit
                WHERE request_id = ?
                ORDER BY id DESC LIMIT 1
                """,
                (request_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], request_id)
        self.assertEqual(row[1], correlation_id)
        self.assertEqual(row[2], "/api/ia-cascade/test")
        self.assertEqual(row[3], "ollama")
        self.assertEqual(row[4], 1)


if __name__ == "__main__":
    unittest.main()
