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
            from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
            from endesive import pdf
            from OpenSSL import crypto
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
            key_c, cert_c, other_certs_c = pkcs12.load_key_and_certificates(
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

        # Convertir a objetos OpenSSL que exige endesive
        try:
            # clave
            if hasattr(key_c, "private_bytes"):
                key_pem = key_c.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
                key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_pem)
            else:
                key = key_c
            # cert principal
            if hasattr(cert_c, "public_bytes"):
                cert_pem = cert_c.public_bytes(Encoding.PEM)
                cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_pem)
            else:
                cert = cert_c
            # cadena
            other_certs = []
            for oc in other_certs_c or []:
                try:
                    if hasattr(oc, "public_bytes"):
                        pem = oc.public_bytes(Encoding.PEM)
                    else:
                        pem = crypto.dump_certificate(crypto.FILETYPE_PEM, oc)
                    other_certs.append(crypto.load_certificate(crypto.FILETYPE_PEM, pem))
                except Exception as e:
                    print(f"⚠️  No se pudo convertir certificado intermedio: {e}")
        except Exception as e:
            err = f"Error convirtiendo certificados a OpenSSL: {e}"
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
                "sigpage": 0,
                "mdalg": "sha256",
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
            if len(signed_pdf) < len(pdf_in) * 0.5:
                raise ValueError("El PDF firmado quedó demasiado pequeño, posible corrupción")
            with open(output_path, 'wb') as f:
                f.write(signed_pdf)

            # Validar que el PDF resultante es legible
            try:
                from PyPDF2 import PdfReader
                PdfReader(output_path)
            except Exception as e:
                err = f"PDF firmado generado pero no es legible ({e})"
                print(f"❌ {err}")
                try:
                    os.remove(output_path)
                except Exception:
                    pass
                return False, err

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
