"""
LexNET Notifications Service
"""
from __future__ import annotations

from datetime import datetime
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

class LexNetNotifications:
    def __init__(self, db_manager):
        self.db = db_manager
        try:
            self._ensure_notifications_schema()
        except Exception:
            # Permite uso del parser sin BD real (tests unitarios / ejecución aislada).
            pass

    def _ensure_notifications_schema(self) -> None:
        """Migración ligera de esquema para campos avanzados LexNET."""
        conn = self.db.get_connection()
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(notifications)")
            existing = {row[1] for row in cur.fetchall()}
            required = {
                "notification_date": "TEXT",
                "deadline_days": "INTEGER",
                "case_type": "TEXT",
                "resolution_type": "TEXT",
                "parties_json": "TEXT",
            }
            for column, col_type in required.items():
                if column in existing:
                    continue
                cur.execute(f"ALTER TABLE notifications ADD COLUMN {column} {col_type}")
            conn.commit()
        finally:
            conn.close()

    def _extract_text_from_pdf(self, file_path: str) -> str:
        text = ""
        try:
            import fitz

            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception:
            text = ""
        return text

    def _extract_text_from_xml(self, file_path: str) -> str:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return " ".join((node.text or "").strip() for node in root.iter() if (node.text or "").strip())
        except Exception:
            return ""

    def _extract_deadline(self, text: str) -> Optional[str]:
        # soporta dd/mm/yyyy y dd-mm-yyyy
        m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](20\d{2})", text)
        if not m:
            return None
        day, month, year = m.group(1).zfill(2), m.group(2).zfill(2), m.group(3)
        return f"{year}-{month}-{day}"

    def _extract_procedure_number(self, text: str) -> str:
        patterns = [
            r"(?:procedimiento|autos|expediente|nig)\s*[:#]?\s*([A-Za-z0-9/\-\.]+)",
            r"\b(\d{2,5}/20\d{2})\b",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                value = m.group(1).strip()
                return value.rstrip(".,;:")
        return ""

    def _extract_court(self, text: str) -> str:
        m = re.search(
            r"(juzgado\s+[^\n\.]{3,120}|audiencia\s+[^\n\.]{3,120}|tribunal\s+[^\n\.]{3,120})",
            text,
            re.IGNORECASE,
        )
        return m.group(1).strip() if m else ""

    def _normalize_spaces(self, value: str) -> str:
        return re.sub(r"\s+", " ", (value or "").strip())

    def _normalize_person_name(self, value: str) -> str:
        cleaned = self._normalize_spaces(value)
        if not cleaned:
            return ""
        # Normaliza "APELLIDO APELLIDO, NOMBRE" -> "Nombre Apellido Apellido"
        if "," in cleaned:
            left, right = [p.strip() for p in cleaned.split(",", 1)]
            if right:
                cleaned = f"{right} {left}"
        return " ".join(part.capitalize() for part in cleaned.split())

    def _extract_notification_date(self, text: str) -> Optional[str]:
        patterns = [
            r"(?:fecha\s+notificaci[oó]n|notificado\s+el|fecha)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]20\d{2})",
            r"\b(\d{1,2}[/-]\d{1,2}[/-]20\d{2})\b",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if not m:
                continue
            raw = m.group(1).replace("-", "/")
            dd, mm, yyyy = raw.split("/")
            return f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"
        return None

    def _extract_case_type(self, text: str) -> str:
        text_l = text.lower()
        type_map = [
            ("juicio verbal", "JUICIO_VERBAL"),
            ("juicio ordinario", "JUICIO_ORDINARIO"),
            ("diligencias previas", "DILIGENCIAS_PREVIAS"),
            ("diligencias urgentes", "DILIGENCIAS_URGENTES"),
            ("ejecución", "EJECUCION"),
            ("procedimiento abreviado", "ABREVIADO"),
        ]
        for key, normalized in type_map:
            if key in text_l:
                return normalized
        return "NO_CLASIFICADO"

    def _extract_resolution_type(self, text: str) -> str:
        text_l = text.lower()
        mapping = [
            ("sentencia", "SENTENCIA"),
            ("auto", "AUTO"),
            ("decreto", "DECRETO"),
            ("providencia", "PROVIDENCIA"),
            ("diligencia", "DILIGENCIA"),
        ]
        for key, norm in mapping:
            if key in text_l:
                return norm
        return "DOCUMENTO"

    def _extract_deadline_days(self, text: str) -> Optional[int]:
        patterns = [
            r"plazo\s+de\s+(\d{1,3})\s+d[ií]as",
            r"en\s+el\s+plazo\s+de\s+(\d{1,3})",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                try:
                    return int(m.group(1))
                except Exception:
                    return None
        return None

    def _extract_parties(self, text: str) -> Dict[str, str]:
        roles = {
            "demandante": r"demandante\s*[:\-]\s*([^\n\.;]{3,120})",
            "demandado": r"demandado\s*[:\-]\s*([^\n\.;]{3,120})",
            "imputado": r"imputado\s*[:\-]\s*([^\n\.;]{3,120})",
            "denunciante": r"denunciante\s*[:\-]\s*([^\n\.;]{3,120})",
            "destinatario": r"destinatario\s*[:\-]\s*([^\n\.;]{3,120})",
        }
        result: Dict[str, str] = {}
        for role, pattern in roles.items():
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                result[role] = self._normalize_person_name(m.group(1))
        return result

    def _normalize_court(self, value: str) -> str:
        cleaned = self._normalize_spaces(value)
        if not cleaned:
            return ""
        replacements = {
            "jdo.": "juzgado",
            "nº": "num",
            "n.": "num",
        }
        low = cleaned.lower()
        for k, v in replacements.items():
            low = low.replace(k, v)
        return " ".join(part.capitalize() for part in low.split())

    def _compute_urgency(self, text: str, deadline: Optional[str]) -> str:
        text_l = text.lower()
        if any(k in text_l for k in ["urgente", "inmediato", "24 horas", "medidas cautelares"]):
            return "CRITICAL"
        if any(k in text_l for k in ["plazo", "recurso", "apercibimiento", "emplazamiento"]):
            return "URGENT"
        if deadline:
            try:
                days = (datetime.strptime(deadline, "%Y-%m-%d").date() - datetime.now().date()).days
                if days <= 2:
                    return "CRITICAL"
                if days <= 7:
                    return "URGENT"
            except Exception:
                pass
        return "NORMAL"
    
    def parse_lexnet_file(self, file_path):
        """Parsear archivo LexNET"""
        ext = Path(file_path).suffix.lower()
        if ext == ".xml":
            raw_text = self._extract_text_from_xml(file_path)
        elif ext == ".pdf":
            raw_text = self._extract_text_from_pdf(file_path)
        else:
            return {'success': False, 'error': 'Formato no soportado'}

        if not raw_text.strip():
            return {'success': False, 'error': 'No se pudo extraer contenido del archivo'}

        deadline = self._extract_deadline(raw_text)
        procedure_number = self._extract_procedure_number(raw_text)
        court = self._normalize_court(self._extract_court(raw_text))
        notification_date = self._extract_notification_date(raw_text)
        case_type = self._extract_case_type(raw_text)
        resolution_type = self._extract_resolution_type(raw_text)
        deadline_days = self._extract_deadline_days(raw_text)
        parties = self._extract_parties(raw_text)
        urgency = self._compute_urgency(raw_text, deadline)

        title = "Notificación LexNET"
        if procedure_number:
            title = f"LexNET {procedure_number}"

        body = raw_text[:2000]
        normalized = {
            'procedure_number': procedure_number or "",
            'court': court or "",
            'notification_date': notification_date,
            'deadline': deadline,
            'deadline_days': deadline_days,
            'case_type': case_type,
            'resolution_type': resolution_type,
            'parties': parties,
        }
        return {
            'success': True,
            'notification_data': {
                'type': 'lexnet',
                'title': title,
                'body': body,
                'deadline': deadline,
                'urgency': urgency,
                'procedure_number': procedure_number,
                'court': court,
                'notification_date': notification_date,
                'case_type': case_type,
                'resolution_type': resolution_type,
                'deadline_days': deadline_days,
                'parties': parties,
                'normalized': normalized,
            }
        }
    
    def save_notification(self, notification_data, user_id):
        """Guardar notificación en BD"""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO notifications
            (
                user_id, type, title, body, deadline, urgency, procedure_number, court,
                notification_date, deadline_days, case_type, resolution_type, parties_json,
                read, archived, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, CURRENT_TIMESTAMP)
            """,
            (
                user_id,
                notification_data.get('type', 'lexnet'),
                notification_data.get('title', 'Notificación LexNET'),
                notification_data.get('body', ''),
                notification_data.get('deadline'),
                notification_data.get('urgency', 'NORMAL'),
                notification_data.get('procedure_number', ''),
                notification_data.get('court', ''),
                notification_data.get('notification_date'),
                notification_data.get('deadline_days'),
                notification_data.get('case_type'),
                notification_data.get('resolution_type'),
                json.dumps(notification_data.get('parties') or {}, ensure_ascii=False),
            ),
        )
        conn.commit()
        notification_id = cur.lastrowid
        conn.close()
        return notification_id
    
    def get_notifications(
        self,
        user_id,
        unread_only=False,
        urgency=None,
        limit=50,
        case_type=None,
        date_from=None,
        date_to=None,
        procedure_number=None,
    ):
        """Obtener notificaciones"""
        conn = self.db.get_connection()
        cur = conn.cursor()

        conditions = ["archived = 0"]
        params: List = []

        if user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)
        if unread_only:
            conditions.append("read = 0")
        if urgency:
            conditions.append("urgency = ?")
            params.append(urgency)
        if case_type:
            conditions.append("case_type = ?")
            params.append(case_type)
        if date_from:
            conditions.append("DATE(created_at) >= DATE(?)")
            params.append(date_from)
        if date_to:
            conditions.append("DATE(created_at) <= DATE(?)")
            params.append(date_to)
        if procedure_number:
            conditions.append("procedure_number LIKE ?")
            params.append(f"%{procedure_number}%")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        cur.execute(
            f"""
            SELECT
                id, user_id, type, title, body, deadline, urgency, procedure_number, court,
                notification_date, deadline_days, case_type, resolution_type, parties_json,
                read, archived, created_at
            FROM notifications
            WHERE {where_clause}
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            """,
            params,
        )
        rows = cur.fetchall()
        conn.close()
        items = []
        for row in rows:
            item = dict(row)
            raw_parties = item.get("parties_json")
            if raw_parties:
                try:
                    item["parties"] = json.loads(raw_parties)
                except Exception:
                    try:
                        import ast
                        item["parties"] = ast.literal_eval(raw_parties)
                    except Exception:
                        item["parties"] = {}
            else:
                item["parties"] = {}
            # Compatibilidad: mantener también el campo crudo para clientes antiguos.
            if "parties_json" not in item:
                item["parties_json"] = "{}"
            items.append(item)
        return items
    
    def mark_as_read(self, notification_id, user_id):
        """Marcar como leída"""
        conn = self.db.get_connection()
        cur = conn.cursor()
        if user_id is not None:
            cur.execute(
                "UPDATE notifications SET read = 1 WHERE id = ? AND user_id = ?",
                (notification_id, user_id),
            )
        else:
            cur.execute("UPDATE notifications SET read = 1 WHERE id = ?", (notification_id,))
        conn.commit()
        updated = cur.rowcount > 0
        conn.close()
        return updated
    
    def get_urgent_count(self, user_id):
        """Contador de urgentes"""
        conn = self.db.get_connection()
        cur = conn.cursor()
        if user_id is not None:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM notifications
                WHERE user_id = ? AND archived = 0 AND read = 0
                AND urgency IN ('CRITICAL', 'URGENT')
                """,
                (user_id,),
            )
        else:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM notifications
                WHERE archived = 0 AND read = 0
                AND urgency IN ('CRITICAL', 'URGENT')
                """
            )
        count = cur.fetchone()[0] or 0
        conn.close()
        return count
