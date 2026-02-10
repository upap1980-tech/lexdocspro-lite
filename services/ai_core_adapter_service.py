import os
import sys
from pathlib import Path

import requests


class _FallbackClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def health(self):
        return requests.get(f"{self.base_url}/api/health", timeout=30).json()

    def health_ocr(self):
        return requests.get(f"{self.base_url}/api/health/ocr", timeout=30).json()

    def chat(self, message, project_id, case_id=None, task_type="chat", allow_cloud=False, model=None):
        payload = {
            "message": message,
            "project_id": project_id,
            "case_id": case_id,
            "task_type": task_type,
            "allow_cloud": allow_cloud,
            "model": model,
        }
        return requests.post(f"{self.base_url}/api/chat", json=payload, timeout=90).json()

    def list_documents(self, project_id, case_id=None):
        params = {"project_id": project_id}
        if case_id is not None and str(case_id).strip() != "":
            params["case_id"] = str(case_id)
        return requests.get(f"{self.base_url}/api/rag/documents", params=params, timeout=60).json()

    def rag_search(self, project_id, case_id, query, top_k=5):
        payload = {"project_id": project_id, "case_id": case_id, "query": query, "top_k": top_k}
        return requests.post(f"{self.base_url}/api/rag/search", json=payload, timeout=60).json()

    def rag_upload(
        self,
        project_id,
        case_id=None,
        document_id="",
        source="upload",
        source_url="",
        page=None,
        content="",
        file_path=None,
    ):
        data = {
            "project_id": project_id,
            "case_id": "" if case_id is None else str(case_id),
            "document_id": document_id,
            "source": source,
            "source_url": source_url,
            "content": content,
        }
        if page is not None:
            data["page"] = str(page)

        files = None
        if file_path:
            path = Path(file_path)
            files = {"file": (path.name, path.open("rb"))}

        try:
            return requests.post(
                f"{self.base_url}/api/rag/upload", data=data, files=files, timeout=120
            ).json()
        finally:
            if files:
                files["file"][1].close()

    def delete_document(self, project_id, document_id, case_id=None):
        payload = {"project_id": project_id, "document_id": document_id, "case_id": case_id}
        return requests.post(f"{self.base_url}/api/rag/delete", json=payload, timeout=60).json()

    def reindex(self):
        return requests.post(f"{self.base_url}/api/rag/reindex", timeout=120).json()


class AICoreAdapterService:
    def __init__(self, base_url=None, sdk_path=None):
        self.base_url = (base_url or os.getenv("AI_CORE_BASE_URL") or "http://localhost:5011").rstrip("/")
        self.sdk_path = sdk_path or os.getenv(
            "AI_CORE_SDK_PATH",
            "/Users/victormfrancisco/Desktop/PROYECTOS/AI-Platform-Core/packages/ai-core-py",
        )
        self.client = self._build_client()

    def _build_client(self):
        sdk_file = Path(self.sdk_path) / "ai_core_sdk.py"
        if sdk_file.exists():
            if self.sdk_path not in sys.path:
                sys.path.append(self.sdk_path)
            try:
                from ai_core_sdk import AIClient  # type: ignore

                return AIClient(self.base_url)
            except Exception:
                pass

        return _FallbackClient(self.base_url)

    def health(self):
        return self.client.health()

    def health_ocr(self):
        if hasattr(self.client, "health_ocr"):
            return self.client.health_ocr()
        return {"available": False, "engine": "tesseract", "path": ""}

    def chat(self, **kwargs):
        return self.client.chat(**kwargs)

    def list_documents(self, project_id, case_id=None):
        return self.client.list_documents(project_id=project_id, case_id=case_id)

    def rag_search(self, project_id, case_id, query, top_k=5):
        return self.client.rag_search(project_id=project_id, case_id=case_id, query=query, top_k=top_k)

    def rag_upload(self, **kwargs):
        return self.client.rag_upload(**kwargs)

    def delete_document(self, project_id, document_id, case_id=None):
        return self.client.delete_document(project_id=project_id, document_id=document_id, case_id=case_id)

    def reindex(self):
        return self.client.reindex()
