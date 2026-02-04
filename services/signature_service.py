"""
Signature Service - Gestión de firmas digitales legalmente vinculantes (v3.1.0)
Soporta PAdES (PDF) utilizando certificados .p12 o .pfx.
"""
import os
from datetime import datetime
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec, append_signature_field

class SignatureService:
    def __init__(self, certificates_dir=None):
        self.certs_dir = certificates_dir or os.path.expanduser("~/Desktop/LEXDOCS_CERTS")
        os.makedirs(self.certs_dir, exist_ok=True)
        
    def sign_pdf(self, input_pdf_path: str, output_pdf_path: str, cert_name: str, passphrase: str) -> bool:
        """
        Firma un PDF con el certificado indicado (formato PAdES).
        """
        cert_path = os.path.join(self.certs_dir, cert_name)
        if not os.path.exists(cert_path):
            raise FileNotFoundError(f"Certificado no encontrado: {cert_path}")

        try:
            # Cargar el firmante desde el archivo P12
            # Usamos SimpleSigner.load_pkcs12 de pyhanko.sign.signers
            signer = signers.SimpleSigner.load_pkcs12(
                pfx_file=cert_path,
                passphrase=passphrase.encode()
            )

            # Preparar el archivo para escritura incremental
            with open(input_pdf_path, 'rb') as inf:
                w = IncrementalPdfFileWriter(inf)
                
                # Añadir campo de firma si no tiene (opcional, pyhanko lo puede crear)
                # append_signature_field(w, SigFieldSpec(sig_field_name='Firma_LexDocs'))
                
                # Firmar
                with open(output_pdf_path, 'wb') as outf:
                    # Usamos el wrapper sign_pdf que maneja la orquestación
                    signers.sign_pdf(
                        w, signers.PdfSignatureMetadata(field_name='Signature1'),
                        signer=signer,
                        output=outf
                    )
            
            return True
        except Exception as e:
            print(f"❌ Error firmando PDF: {str(e)}")
            return False

    def list_available_certificates(self):
        """Listar certificados disponibles en la carpeta de seguridad"""
        return [f for f in os.listdir(self.certs_dir) if f.endswith(('.p12', '.pfx'))]

    def verify_signature(self, pdf_path: str):
        """
        Verifica la validez de las firmas en un PDF.
        """
        from pyhanko.pdf_utils.reader import PdfFileReader
        from pyhanko.sign.validation import validate_pdf_signature
        
        try:
            with open(pdf_path, 'rb') as f:
                reader = PdfFileReader(f)
                if not reader.embedded_signatures:
                    return {"status": "no_signatures", "valid": False}
                
                results = []
                for sig in reader.embedded_signatures:
                    status = validate_pdf_signature(sig)
                    results.append({
                        "field": sig.field_name,
                        "valid": status.valid,
                        "integrity": status.intact,
                        "signer": status.signer_cert.subject.human_friendly if status.signer_cert else "Desconocido"
                    })
                
                return {"status": "verified", "results": results}
        except Exception as e:
            return {"status": "error", "error": str(e)}
