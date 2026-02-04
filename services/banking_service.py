"""
Banking Service - Integración con bancos españoles (v2.3.0)
Soporta 11 bancos principales mediante arquitectura de adaptadores.
"""
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

class BankAdapter(ABC):
    """Clase base para adaptadores bancarios"""
    
    @abstractmethod
    def parse_statement(self, content: str) -> List[Dict]:
        """Convertir extracto bancario a formato normalizado"""
        pass

    @property
    @abstractmethod
    def bank_id(self) -> str:
        """Identificador único del banco"""
        pass

class SantanderAdapter(BankAdapter):
    @property
    def bank_id(self) -> str: return "SANTANDER"
    def parse_statement(self, content: str) -> List[Dict]:
        """Parser básico para Santander (v2.3)"""
        transactions = []
        # Patrón típico: DD-MM-YYYY  Descripción  Importe
        pattern = r'(\d{2}-\d{2}-\d{4})\s+(.+?)\s+(-?[\d\.,]+)'
        matches = re.finditer(pattern, content)
        for m in matches:
            try:
                amt = float(m.group(3).replace('.', '').replace(',', '.'))
                transactions.append({
                    "date": m.group(1),
                    "description": m.group(2).strip(),
                    "amount": amt,
                    "bank": self.bank_id
                })
            except: continue
        return transactions

class BBVAAdapter(BankAdapter):
    @property
    def bank_id(self) -> str: return "BBVA"
    def parse_statement(self, content: str) -> List[Dict]:
        """Parser básico para BBVA (v2.3)"""
        transactions = []
        # Patrón típico: DD/MM/YYYY  Concepto  Importe
        pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?[\d\.,]+)'
        matches = re.finditer(pattern, content)
        for m in matches:
            try:
                amt = float(m.group(3).replace('.', '').replace(',', '.'))
                transactions.append({
                    "date": m.group(1),
                    "description": m.group(2).strip(),
                    "amount": amt,
                    "bank": self.bank_id
                })
            except: continue
        return transactions

class CaixaBankAdapter(BankAdapter):
    @property
    def bank_id(self) -> str: return "CAIXABANK"
    def parse_statement(self, content: str) -> List[Dict]:
        """
        Parser Robusto para CaixaBank (v2.3 Phase 1)
        Soporta formatos comunes de extractos exportados.
        """
        transactions = []
        import re
        
        # Patrón 1: DD/MM/YYYY DD/MM/YYYY DESCRIPCION IMPORTE SALDO
        # Ejemplo: 05/02/2026 05/02/2026 TRANSFERENCIA PENDIENTE -150,00 1.250,50
        pattern = r'(\d{2}/\d{2}/\d{4})\s+\d{2}/\d{2}/\d{4}\s+(.+?)\s+(-?[\d\.,]+)\s+(-?[\d\.,]+)'
        
        matches = re.finditer(pattern, content)
        for m in matches:
            try:
                date = m.group(1)
                desc = m.group(2).strip()
                # Limpiar importe (quitar puntos de miles, cambiar coma por punto)
                amt_str = m.group(3).replace('.', '').replace(',', '.')
                amt = float(amt_str)
                bal_str = m.group(4).replace('.', '').replace(',', '.')
                balance = float(bal_str)
                
                transactions.append({
                    "date": date,
                    "description": desc,
                    "amount": amt,
                    "balance": balance,
                    "bank": self.bank_id
                })
            except ValueError:
                continue
                
        # Patrón 2: Fallback para descripción simple y monto
        if not transactions:
            pattern_fallback = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?[\d\.,]+)'
            matches = re.finditer(pattern_fallback, content)
            for m in matches:
                try:
                    amt = float(m.group(3).replace('.', '').replace(',', '.'))
                    transactions.append({
                        "date": m.group(1),
                        "description": m.group(2).strip(),
                        "amount": amt,
                        "bank": self.bank_id
                    })
                except: continue
                
        return transactions

class SabadellAdapter(BankAdapter):
    @property
    def bank_id(self) -> str: return "SABADELL"
    def parse_statement(self, content: str) -> List[Dict]:
        """Parser para Sabadell (v2.3)"""
        transactions = []
        # Patrón: Fecha Valor | Fecha Operación | Concepto | Importe | Saldo
        pattern = r'(\d{2}/\d{2}/\d{4})\s+\d{2}/\d{2}/\d{4}\s+(.+?)\s+(-?[\d\.,]+)\s+(-?[\d\.,]+)'
        matches = re.finditer(pattern, content)
        for m in matches:
            try:
                amt = float(m.group(3).replace('.', '').replace(',', '.'))
                transactions.append({
                    "date": m.group(1),
                    "description": m.group(2).strip(),
                    "amount": amt,
                    "bank": self.bank_id,
                    "bank": self.bank_id
                })
            except: continue
        return transactions

class BankinterAdapter(BankAdapter):
    @property
    def bank_id(self) -> str: return "BANKINTER"
    def parse_statement(self, content: str) -> List[Dict]:
        """Parser para Bankinter (v2.3)"""
        transactions = []
        # Patrón: Fecha | Concepto | Cargo/Abono | Saldo
        pattern = r'(\d{2}-\d{2}-\d{4})\s+(.+?)\s+(-?[\d\.,]+)\s+([\d\.,]+)'
        matches = re.finditer(pattern, content)
        for m in matches:
            try:
                amt = float(m.group(3).replace('.', '').replace(',', '.'))
                transactions.append({
                    "date": m.group(1),
                    "description": m.group(2).strip(),
                    "amount": amt,
                    "bank": self.bank_id,
                    "bank": self.bank_id
                })
            except: continue
        return transactions

class UnicajaAdapter(BankAdapter):
    @property
    def bank_id(self) -> str: return "UNICAJA"
    def parse_statement(self, content: str) -> List[Dict]:
        """Parser para Unicaja (v2.3)"""
        transactions = []
        # Patrón: DD/MM/AAAA  DESCRIPCIÓN  IMPORTE
        pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?[\d\.,]+)'
        matches = re.finditer(pattern, content)
        for m in matches:
            try:
                amt = float(m.group(3).replace('.', '').replace(',', '.'))
                transactions.append({
                    "date": m.group(1),
                    "description": m.group(2).strip(),
                    "amount": amt,
                    "bank": self.bank_id,
                    "bank": self.bank_id
                })
            except: continue
        return transactions

class AbancaAdapter(BankAdapter):
    @property
    def bank_id(self) -> str: return "ABANCA"
    def parse_statement(self, content: str) -> List[Dict]:
        """Parser para Abanca (v2.3)"""
        transactions = []
        # Patrón: DD-MM-AA  CONCEPTO  EUROS
        pattern = r'(\d{2}-\d{2}-\d{2})\s+(.+?)\s+(-?[\d\.,]+)'
        matches = re.finditer(pattern, content)
        for m in matches:
            try:
                # Corregir año de 2 dígitos a 4 si es necesario
                date_str = m.group(1)
                if len(date_str.split('-')[-1]) == 2:
                    date_str = date_str[:-2] + "20" + date_str[-2:]
                
                amt = float(m.group(3).replace('.', '').replace(',', '.'))
                transactions.append({
                    "date": date_str,
                    "description": m.group(2).strip(),
                    "amount": amt,
                    "bank": self.bank_id,
                    "bank": self.bank_id
                })
            except: continue
        return transactions

class CajamarAdapter(BankAdapter):
    @property
    def bank_id(self) -> str: return "CAJAMAR"
    def parse_statement(self, content: str) -> List[Dict]:
        """Parser para Cajamar (v2.3)"""
        transactions = []
        pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?[\d\.,]+)'
        matches = re.finditer(pattern, content)
        for m in matches:
            try:
                amt = float(m.group(3).replace('.', '').replace(',', '.'))
                transactions.append({
                    "date": m.group(1),
                    "description": m.group(2).strip(),
                    "amount": amt,
                    "bank": self.bank_id
                })
            except: continue
        return transactions

class IbercajaAdapter(BankAdapter):
    @property
    def bank_id(self) -> str: return "IBERCAJA"
    def parse_statement(self, content: str) -> List[Dict]:
        """Parser para Ibercaja (v2.3)"""
        transactions = []
        pattern = r'(\d{2}-\d{2}-\d{4})\s+(.+?)\s+(-?[\d\.,]+)'
        matches = re.finditer(pattern, content)
        for m in matches:
            try:
                amt = float(m.group(3).replace('.', '').replace(',', '.'))
                transactions.append({
                    "date": m.group(1),
                    "description": m.group(2).strip(),
                    "amount": amt,
                    "bank": self.bank_id
                })
            except: continue
        return transactions

class KutxabankAdapter(BankAdapter):
    @property
    def bank_id(self) -> str: return "KUTXABANK"
    def parse_statement(self, content: str) -> List[Dict]:
        """Parser para Kutxabank (v2.3)"""
        transactions = []
        pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?[\d\.,]+)'
        matches = re.finditer(pattern, content)
        for m in matches:
            try:
                amt = float(m.group(3).replace('.', '').replace(',', '.'))
                transactions.append({
                    "date": m.group(1),
                    "description": m.group(2).strip(),
                    "amount": amt,
                    "bank": self.bank_id
                })
            except: continue
        return transactions

class OpenbankAdapter(BankAdapter):
    @property
    def bank_id(self) -> str: return "OPENBANK"
    def parse_statement(self, content: str) -> List[Dict]:
        """Parser para Openbank (v2.3)"""
        transactions = []
        pattern = r'(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?[\d\.,]+)'
        matches = re.finditer(pattern, content)
        for m in matches:
            try:
                amt = float(m.group(3).replace('.', '').replace(',', '.'))
                transactions.append({
                    "date": m.group(1),
                    "description": m.group(2).strip(),
                    "amount": amt,
                    "bank": self.bank_id
                })
            except: continue
        return transactions

class BankingService:
    """Servicio central de banca"""
    
    def __init__(self, db_manager=None):
        self.db = db_manager
        self.adapters = {
            "SANTANDER": SantanderAdapter(),
            "BBVA": BBVAAdapter(),
            "CAIXABANK": CaixaBankAdapter(),
            "SABADELL": SabadellAdapter(),
            "BANKINTER": BankinterAdapter(),
            "UNICAJA": UnicajaAdapter(),
            "ABANCA": AbancaAdapter(),
            "CAJAMAR": CajamarAdapter(),
            "IBERCAJA": IbercajaAdapter(),
            "KUTXABANK": KutxabankAdapter(),
            "OPENBANK": OpenbankAdapter()
        }
        
    def get_supported_banks(self) -> List[str]:
        return list(self.adapters.keys())

    def import_transactions(self, bank_id: str, content: str) -> Dict:
        """Importar transacciones usando el adaptador correspondiente"""
        if bank_id not in self.adapters:
            return {"success": False, "error": f"Banco {bank_id} no soportado"}
        
        adapter = self.adapters[bank_id]
        try:
            transactions = adapter.parse_statement(content)
            # Aquí iría la lógica para guardar en DB
            # self._save_to_db(transactions)
            return {
                "success": True, 
                "count": len(transactions),
                "bank": bank_id
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
