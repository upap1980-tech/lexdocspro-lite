"""
Signature Service - Firma digital de documentos PDF
Versión stub para v2.3.1
"""
import os
import io
import tempfile

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

        # Firma con pyHanko (más robusto)
        try:
            from pyhanko.sign import signers
            from pyhanko.sign.fields import SigFieldSpec
        except Exception as e:
            err = f"Dependencias pyHanko no disponibles: {e}"
            print(f"❌ {err}")
            return False, err

        # Intentar varias combinaciones para compatibilidad entre versiones pyHanko.
        load_errors = []
        simple_signer = None
        for cpwd in [passphrase.encode() if passphrase else None, None]:
            for loader in (
                lambda: signers.SimpleSigner.load_pkcs12(cert_path, passphrase=cpwd),
                lambda: signers.SimpleSigner.load_pkcs12(pfx_file=cert_path, passphrase=cpwd),
            ):
                try:
                    simple_signer = loader()
                    if simple_signer:
                        break
                except Exception as e:
                    load_errors.append(str(e))
            if simple_signer:
                break
        if not simple_signer:
            err = f"Error cargando PKCS#12 con pyHanko: {' | '.join(load_errors[-2:])}"
            print(f"❌ {err}")
            return False, err

        try:
            with open(input_path, 'rb') as inf:
                pdf_in = inf.read()
        except Exception as e:
            err = f"No se pudo leer PDF a firmar: {e}"
            print(f"❌ {err}")
            return False, err

        try:
            meta = signers.PdfSignatureMetadata(field_name="Sig1", md_algorithm="sha256")
            from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
            from pyhanko.sign.signers import PdfSigner
            from pyhanko.stamp import TextStampStyle

            # Mantener stream con seek/read para compatibilidad entre versiones pyHanko.
            input_stream = io.BytesIO(pdf_in)
            writer = IncrementalPdfFileWriter(input_stream)
            bio_out = io.BytesIO()
            field_spec = SigFieldSpec("Sig1", on_page=0, box=(36, 36, 260, 120))
            pdf_signer = PdfSigner(
                signature_meta=meta,
                signer=simple_signer,
                stamp_style=TextStampStyle(),
                new_field_spec=field_spec,
            )
            pdf_signer.sign_pdf(
                writer,
                existing_fields_only=False,
                output=bio_out,
            )
            out = bio_out.getvalue()
            self._write_and_validate_pdf(output_path, out, len(pdf_in))

            print(f"✅ PDF firmado en {output_path}")
            return True, None
        except Exception as e:
            # Fallback de compatibilidad para algunas variantes pyHanko.
            try:
                from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
                writer = IncrementalPdfFileWriter(io.BytesIO(pdf_in))
                out_buf = io.BytesIO()
                signers.sign_pdf(
                    writer,
                    signature_meta=meta,
                    signer=simple_signer,
                    new_field_spec=SigFieldSpec("Sig1", on_page=0, box=(36, 36, 260, 120)),
                    existing_fields_only=False,
                    output=out_buf,
                )
                out = out_buf.getvalue()
                self._write_and_validate_pdf(output_path, out, len(pdf_in))
                print(f"✅ PDF firmado en {output_path} (fallback)")
                return True, None
            except Exception as e2:
                err = f"Error firmando PDF: {e} | fallback: {e2}"
                print(f"❌ {err}")
                return False, err

    def _write_and_validate_pdf(self, output_path: str, data: bytes, input_size: int):
        if not data or len(data) < max(256, int(input_size * 0.5)):
            raise ValueError("El PDF firmado quedó demasiado pequeño, posible corrupción")
        if not data.startswith(b"%PDF-"):
            raise ValueError("Salida no tiene cabecera PDF válida")
        if b"%%EOF" not in data[-2048:]:
            raise ValueError("Salida PDF no contiene marcador EOF")
        # Validación de legibilidad con al menos un parser robusto.
        self._assert_pdf_readable(data)

        # Escritura atómica para evitar dejar archivos corruptos a medio generar.
        out_dir = os.path.dirname(output_path) or "."
        os.makedirs(out_dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix=".signed_", suffix=".pdf", dir=out_dir)
        try:
            with os.fdopen(fd, "wb") as outf:
                outf.write(data)
            os.replace(tmp_path, output_path)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def _assert_pdf_readable(self, data: bytes):
        errors = []
        # PyMuPDF primero (suele ser más tolerante y rápido)
        try:
            import fitz  # PyMuPDF
            with fitz.open(stream=data, filetype="pdf") as doc:
                if doc.page_count < 1:
                    raise ValueError("PDF sin páginas")
            return
        except Exception as e:
            errors.append(f"fitz: {e}")

        # Fallback con pypdf / PyPDF2
        for mod_name in ("pypdf", "PyPDF2"):
            try:
                mod = __import__(mod_name)
                reader_cls = getattr(mod, "PdfReader", None)
                if reader_cls is None:
                    continue
                reader = reader_cls(io.BytesIO(data))
                if len(reader.pages) < 1:
                    raise ValueError("PDF sin páginas")
                return
            except Exception as e:
                errors.append(f"{mod_name}: {e}")
        raise ValueError("PDF firmado no legible: " + " | ".join(errors[-2:]))
    
    def verify_signature(self, pdf_path):
        """Verificar firma de un PDF"""
        try:
            if not os.path.exists(pdf_path):
                return {'signed': False, 'valid': False, 'error': 'Archivo no encontrado'}
            with open(pdf_path, "rb") as f:
                data = f.read()
            self._assert_pdf_readable(data)
            # Verificación estructural mínima: presencia de diccionario de firma.
            signed = (b"/Type /Sig" in data) or (b"/Contents" in data and b"/ByteRange" in data)
            return {
                'signed': bool(signed),
                'valid': bool(signed),
                'signer': None,
                'timestamp': None,
            }
        except Exception as e:
            return {
                'signed': False,
                'valid': False,
                'error': str(e),
            }
