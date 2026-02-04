import sqlite3
import os

class LiteRAGSkill:
    """
    Retrieval Augmented Generation (Lite Version)
    Usa la base de datos SQL para buscar documentos relevantes por keywords 
    y recuperar su contenido (OCR) para contexto.
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def retrieve_context(self, query, w_limit=3):
        """
        Recupera fragmentos de texto relevantes.
        Estrategia LITE: Búsqueda LIKE en metadata o contenido si estuviera indexado.
        Aquí buscamos en 'saved_documents' por nombre o cliente.
        """
        # Extraer keywords simples (excluyendo stop words básicas)
        stop_words = {'el', 'la', 'de', 'en', 'y', 'a', 'que', 'es', 'un', 'una'}
        keywords = [w for w in query.lower().split() if w not in stop_words and len(w) > 3]
        
        if not keywords:
            return ""
            
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # Construir query dinámica
        conditions = []
        params = []
        for kw in keywords:
            conditions.append("(filename LIKE ? OR client_name LIKE ? OR doc_type LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])
            
        sql = f"SELECT filename, file_path, client_name FROM saved_documents WHERE {' OR '.join(conditions)} LIMIT {w_limit}"
        
        try:
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            context_parts = []
            for row in results:
                # En un sistema real leeríamos el contenido. Aquí simulamos o leemos si existe archivo txt asociado
                # Para LITE, devolvemos metadata como contexto "Sabemos que existe un documento..."
                context_parts.append(f"[DOCUMENTO RELACIONADO: {row['filename']} (Cliente: {row['client_name']})]")
                
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"RAG Error: {e}")
            return ""
        finally:
            conn.close()
