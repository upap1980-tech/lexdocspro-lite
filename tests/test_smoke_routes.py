import unittest

import run


class TestSmokeRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = run.app
        cls.client = cls.app.test_client()

    def assert_non_500(self, response, path):
        self.assertLess(
            response.status_code,
            500,
            msg=f"{path} devolvió {response.status_code}",
        )

    def test_core_get_routes_non_500(self):
        endpoints = [
            "/api/health",
            "/api/health/ready",
            "/api/status/overview",
            "/api/pwa/status",
            "/api/files",
            "/api/ai/providers",
            "/api/documents/templates",
            "/api/document/types",
            "/api/dashboard/stats",
            "/api/dashboard/stats-detailed",
            "/api/autoprocessor/status",
            "/api/autoprocessor/log",
            "/api/ia-cascade/stats-public",
            "/api/ia-cascade/providers-public",
            "/api/ia-cascade/status",
            "/api/watchdog-status",
            "/api/autoprocesos/logs",
            "/api/lexnet-urgent",
            "/api/alerts/history",
            "/api/alerts/status",
            "/api/firma/status",
            "/api/banking/institutions",
            "/api/banking/stats",
            "/api/banking/transactions",
            "/api/usuarios/equipo",
            "/api/usuarios/stats",
            "/api/analytics/detailed",
            "/api/expedientes/listar",
            "/api/config/get",
            "/api/deploy/status",
            "/api/pdf/preview-data",
            "/api/ai/status",
            "/api/ia-cascade/providers",
            "/api/ia-cascade/stats",
        ]
        for path in endpoints:
            with self.subTest(path=path):
                res = self.client.get(path)
                if path == "/api/health/ready":
                    self.assertIn(
                        res.status_code,
                        (200, 503),
                        msg=f"{path} devolvió {res.status_code}",
                    )
                    continue
                self.assert_non_500(res, path)

    def test_core_post_routes_non_500(self):
        cases = [
            ("/api/ocr", {"filename": "missing.pdf"}),
            ("/api/ocr/upload", None),
            ("/api/document/propose-save", {}),
            ("/api/document/confirm-save", {}),
            ("/api/document/smart-analyze", {}),
            ("/api/autoprocessor/scan", {}),
            ("/api/autoprocessor/start", {}),
            ("/api/autoprocessor/stop", {}),
            ("/api/autoprocessor/reset", {}),
            ("/api/ia-cascade/test", {"prompt": "hola", "provider": "cascade"}),
            ("/api/ia-cascade/reset-stats", {}),
            ("/api/ia-cascade/query", {"prompt": "hola"}),
            ("/api/ia/consultar", {"prompt": "hola", "provider": "ollama"}),
            ("/api/ia/agent-task", {"task": "probar agente"}),
            ("/api/autoprocesos/toggle", {"action": "start"}),
            ("/api/alerts/config", {"email": "admin@lexdocs.com"}),
            ("/api/alerts/test-email", {"to_email": "admin@lexdocs.com"}),
            ("/api/firma/ejecutar", {"doc_id": "test-doc"}),
            ("/api/usuarios/registrar", {"nombre": "Usuario Test"}),
            ("/api/ai/models", {"model": "lexdocs-legal-pro"}),
            ("/api/lexnet/analizar-plazo", {"dias": 20}),
            ("/api/config/save", {"ollama_model": "lexdocs-legal-pro", "ia_fallback": True}),
        ]
        for path, payload in cases:
            with self.subTest(path=path):
                if payload is None:
                    res = self.client.post(path)
                else:
                    res = self.client.post(path, json=payload)
                self.assert_non_500(res, path)

    def test_existing_autoprocesador_routes_non_500(self):
        endpoints = [
            "/api/autoprocesador/stats",
            "/api/autoprocesador/cola-revision",
            "/api/autoprocesador/procesados-hoy",
            "/api/autoprocesador/clientes",
        ]
        for path in endpoints:
            with self.subTest(path=path):
                res = self.client.get(path)
                self.assert_non_500(res, path)


if __name__ == "__main__":
    unittest.main()
