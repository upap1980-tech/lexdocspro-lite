"""
Signature Service - Firma digital de documentos PDF
Versión stub para v2.3.1
"""
import os

CERTS_PATH_DEFAULT = os.path.expanduser("~/Desktop/LEXDOCS_CERTS")


class SignatureService:
    def __init__(self, certificates_path: str = CERTS_PATH_DEFAULT):
        self.certificates_path = os.path.expanduser(certificates_path)
        os.makedirs(self.certificates_path, exist_ok=True)
    
    def list_available_certificates(self):
        """Listar certificados .p12 disponibles"""
        try:
            if not os.path.exists(self.certificates_path):
                return []
            
            certs = []
            for file in os.listdir(self.certificates_path):
                if file.lower().endswith('.p12'):
                    certs.append({
                        'name': file,
                        'path': os.path.join(self.certificates_path, file)
                    })
            
            return certs
        except Exception as e:
            print(f"Error listando certificados: {e}")
            return []
    
    def sign_pdf(self, input_path, output_path, cert_name, passphrase):
        """
        Firmar PDF con certificado PKCS#12 usando endesive (CMS).
        """
        try:
            from cryptography.hazmat.primitives.serialization import pkcs12
            from endesive import pdf
            import datetime
        except Exception as e:
            err = f"Dependencias de firma no disponibles: {e}"
            print(f"❌ {err}")
            return False, err

        cert_path = os.path.join(self.certificates_path, cert_name)
        if not os.path.exists(cert_path):
            err = f"Certificado no encontrado: {cert_path}"
            print(f"❌ {err}")
            return False, err

        # Cargar PKCS12 con passphrase (permitir vacío si no se indicó)
        try:
            data = open(cert_path, 'rb').read()
            key, cert, other_certs = pkcs12.load_key_and_certificates(
                data,
                passphrase.encode() if passphrase else None,
            )
        except Exception as e:
            if not passphrase:
                err = "El certificado requiere passphrase. Indícala e inténtalo de nuevo."
            else:
                err = f"Error cargando PKCS#12 ({cert_path}): {e}"
            print(f"❌ {err}")
            return False, err

        try:
            with open(input_path, 'rb') as f:
                pdf_in = f.read()
        except Exception as e:
            err = f"No se pudo leer PDF a firmar: {e}"
            print(f"❌ {err}")
            return False, err

        try:
            date = datetime.datetime.utcnow()
            dct = {
                "sigflags": 3,
                "contact": "LexDocsPro",
                "location": "ES",
                "signingdate": date.strftime("D:%Y%m%d%H%M%S+00'00'"),
                "reason": "LexDocsPro digital signature",
                "signature": "Signature1",
            }
            signed_pdf = pdf.cms.sign(
                pdf_in,
                dct,
                key,
                cert,
                othercerts=other_certs,
                algomd="sha256",
            )
            with open(output_path, 'wb') as f:
                f.write(signed_pdf)
            print(f"✅ PDF firmado en {output_path}")
            return True, None
        except Exception as e:
            err = f"Error firmando PDF: {e}"
            print(f"❌ {err}")
            return False, err
    
    def verify_signature(self, pdf_path):
        """Verificar firma de un PDF"""
        # Stub - en producción verificaría la firma real
        return {
            'signed': False,
            'valid': False,
            'signer': None,
            'timestamp': None
        }
