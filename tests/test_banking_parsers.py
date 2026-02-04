import sys
import os
import unittest

# Path adjustment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.banking_service import BankingService

class TestBankingParsers(unittest.TestCase):
    def setUp(self):
        self.service = BankingService()

    def test_caixabank_parser_standard(self):
        """Verificar formato estándar de CaixaBank"""
        content = """
        05/02/2026 05/02/2026 TRANSFERENCIA PENDIENTE -150,00 1.250,50
        06/02/2026 06/02/2026 NOMINA EMPRESA SL 2.100,00 3.350,50
        08/02/2026 08/02/2026 PAGO NOTARIA -3.500,00 -195,49
        """
        adapter = self.service.adapters["CAIXABANK"]
        transactions = adapter.parse_statement(content)
        self.assertEqual(len(transactions), 3)
        self.assertEqual(transactions[0]["amount"], -150.0)
        self.assertTrue(transactions[2]["priority_alert"])

    def test_sabadell_parser(self):
        """Verificar formato Sabadell"""
        content = "10/02/2026 10/02/2026 RECIBO AUTONOMOS -299,90 1.500,00"
        adapter = self.service.adapters["SABADELL"]
        transactions = adapter.parse_statement(content)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]["amount"], -299.9)

    def test_abanca_parser(self):
        """Verificar formato Abanca (año 2 dígitos)"""
        content = "12-02-26 COMPRA SUPERMERCADO -45,50"
        adapter = self.service.adapters["ABANCA"]
        transactions = adapter.parse_statement(content)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]["date"], "12-02-2026")
        self.assertEqual(transactions[0]["amount"], -45.5)

    def test_bankinter_parser(self):
        """Verificar formato Bankinter"""
        content = "15-02-2026 INTERESES CUENTA 5,20 10.005,20"
        adapter = self.service.adapters["BANKINTER"]
        transactions = adapter.parse_statement(content)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]["amount"], 5.2)

    def test_bbva_parser(self):
        """Verificar formato básico BBVA"""
        content = "10/02/2026  PAGO LUZ  -85,50"
        adapter = self.service.adapters["BBVA"]
        transactions = adapter.parse_statement(content)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]["amount"], -85.5)

if __name__ == '__main__':
    unittest.main()
