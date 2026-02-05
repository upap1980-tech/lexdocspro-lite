import os
import tempfile
import unittest

from services.lexnet_notifications import LexNetNotifications


class _DummyDB:
    def get_connection(self):
        raise RuntimeError("No DB required for parse tests")


class TestLexNetParser(unittest.TestCase):
    def setUp(self):
        self.service = LexNetNotifications(db_manager=_DummyDB())

    def _write_xml(self, body_text: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".xml", dir="/tmp")
        os.close(fd)
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<root>
  <mensaje>{body_text}</mensaje>
</root>
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml_content)
        return path

    def test_extracts_extended_legal_fields(self):
        source = (
            "JUZGADO DE PRIMERA INSTANCIA Nº 7 DE LAS PALMAS. "
            "Procedimiento: 123/2026. "
            "Fecha notificación: 05/02/2026. "
            "Plazo de 20 días para contestar demanda. "
            "Demandante: PEREZ GARCIA, MARIA. "
            "Demandado: LOPEZ SANCHEZ, JUAN. "
            "Juicio verbal. Sentencia."
        )
        xml_path = self._write_xml(source)
        try:
            result = self.service.parse_lexnet_file(xml_path)
        finally:
            if os.path.exists(xml_path):
                os.remove(xml_path)

        self.assertTrue(result.get("success"))
        data = result["notification_data"]
        self.assertEqual(data.get("procedure_number"), "123/2026")
        self.assertEqual(data.get("case_type"), "JUICIO_VERBAL")
        self.assertEqual(data.get("resolution_type"), "SENTENCIA")
        self.assertEqual(data.get("notification_date"), "2026-02-05")
        self.assertEqual(data.get("deadline_days"), 20)
        self.assertIn("Juzgado", data.get("court", ""))
        self.assertEqual(data.get("parties", {}).get("demandante"), "Maria Perez Garcia")
        self.assertEqual(data.get("parties", {}).get("demandado"), "Juan Lopez Sanchez")

    def test_rejects_unsupported_format(self):
        fd, path = tempfile.mkstemp(suffix=".txt", dir="/tmp")
        os.close(fd)
        try:
            result = self.service.parse_lexnet_file(path)
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.assertFalse(result.get("success"))
        self.assertIn("Formato no soportado", result.get("error", ""))


if __name__ == "__main__":
    unittest.main()
