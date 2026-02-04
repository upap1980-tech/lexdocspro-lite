class BankingService:
    def __init__(self, *args, **kwargs): pass
    def __getattr__(self, name):
        def handler(*args, **kwargs):
            return {"success": False, "error": "Banking module not available in LITE"}
        return handler
