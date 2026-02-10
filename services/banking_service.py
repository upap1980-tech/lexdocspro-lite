"""
Banking Service - Real Open Banking integration (GoCardless/Nordigen).
"""
from __future__ import annotations

import os
from datetime import datetime

import requests


class BankingService:
    def __init__(self):
        self.provider = os.getenv("BANKING_PROVIDER", "gocardless").strip().lower()
        self.base_url = os.getenv("BANKING_BASE_URL", "https://bankaccountdata.gocardless.com/api/v2").rstrip("/")
        self.secret_id = os.getenv("BANKING_GOCARDLESS_SECRET_ID", "").strip()
        self.secret_key = os.getenv("BANKING_GOCARDLESS_SECRET_KEY", "").strip()
        self.country = os.getenv("BANKING_COUNTRY", "ES").strip().upper()
        self.account_ids = [x.strip() for x in os.getenv("BANKING_ACCOUNT_IDS", "").split(",") if x.strip()]
        self.timeout = int(os.getenv("BANKING_TIMEOUT", "20"))
        self._access_token = None

    def _configured(self) -> tuple[bool, str]:
        if self.provider != "gocardless":
            return False, f"Proveedor bancario no soportado: {self.provider}"
        if not self.secret_id or not self.secret_key:
            return False, "Faltan BANKING_GOCARDLESS_SECRET_ID / BANKING_GOCARDLESS_SECRET_KEY"
        return True, ""

    def _token(self) -> str:
        if self._access_token:
            return self._access_token
        url = f"{self.base_url}/token/new/"
        resp = requests.post(
            url,
            json={"secret_id": self.secret_id, "secret_key": self.secret_key},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("access")
        if not token:
            raise RuntimeError("No se obtuvo access token de GoCardless")
        self._access_token = token
        return token

    def _headers(self):
        return {
            "Authorization": f"Bearer {self._token()}",
            "Accept": "application/json",
        }

    def get_institutions(self, country: str | None = None):
        ok, err = self._configured()
        if not ok:
            return {"success": False, "error": err, "institutions": []}
        c = (country or self.country).upper()
        url = f"{self.base_url}/institutions/"
        resp = requests.get(url, params={"country": c}, headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", data if isinstance(data, list) else [])
        institutions = []
        for item in results:
            institutions.append(
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "bic": item.get("bic"),
                    "countries": item.get("countries", []),
                    "status": "available",
                }
            )
        return {"success": True, "institutions": institutions}

    def get_transactions(self, limit: int = 50):
        ok, err = self._configured()
        if not ok:
            return {"success": False, "error": err, "transactions": []}
        if not self.account_ids:
            return {"success": False, "error": "BANKING_ACCOUNT_IDS vacío", "transactions": []}

        tx = []
        for account_id in self.account_ids:
            url = f"{self.base_url}/accounts/{account_id}/transactions/"
            resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            booked = data.get("transactions", {}).get("booked", [])
            for row in booked[:limit]:
                tx.append(
                    {
                        "account_id": account_id,
                        "date": row.get("bookingDate") or row.get("valueDate"),
                        "concept": row.get("remittanceInformationUnstructured") or row.get("additionalInformation"),
                        "amount": float(row.get("transactionAmount", {}).get("amount", 0)),
                        "currency": row.get("transactionAmount", {}).get("currency"),
                        "bank": row.get("debtorName") or row.get("creditorName") or "N/A",
                    }
                )
        tx.sort(key=lambda x: x.get("date") or "", reverse=True)
        return {"success": True, "transactions": tx[:limit]}

    def get_stats(self):
        institutions = self.get_institutions(self.country)
        transactions = self.get_transactions(limit=200)
        if not institutions.get("success") and not transactions.get("success"):
            return {
                "success": False,
                "error": institutions.get("error") or transactions.get("error") or "No configurado",
                "stats": {
                    "bancos_activos": 0,
                    "pendientes_conciliar": 0,
                    "ultimo_sincro": None,
                    "alerts_criticas": 0,
                },
            }
        tx = transactions.get("transactions", [])
        stats = {
            "bancos_activos": len(institutions.get("institutions", [])),
            "pendientes_conciliar": len(tx),
            "ultimo_sincro": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "alerts_criticas": 0,
        }
        return {"success": True, "stats": stats}
