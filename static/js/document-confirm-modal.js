/**
 * Document Confirm Modal - Flujo interactivo de confirmación de documentos
 * 4 Pasos: Preview PDF → Editar Datos → Selector de Ruta → Confirmar
 */

class DocumentConfirmModal {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.tempFilePath = null;
        this.extractedData = {};
        this.editedData = {};
        this.pathOptions = [];
        this.selectedPath = null;
        this.textPreview = '';

        this.init();
    }

    init() {
        // Crear estructura del modal
        this.createModalHTML();
        this.attachEventListeners();
    }

    createModalHTML() {
        const modalHTML = `
            <div id="documentConfirmModal" class="modal hidden">
                <div class="modal-overlay"></div>
                <div class="modal-content large">
                    <!-- Header -->
                    <div class="modal-header">
                        <h2>📄 Confirmar y Guardar Documento</h2>
                        <button class="close-modal" onclick="documentModal.close()">&times;</button>
                    </div>
                    
                    <!-- Progress Steps -->
                    <div class="progress-steps">
                        <div class="step active" data-step="1">
                            <span class="step-number">1</span>
                            <span class="step-label">Preview</span>
                        </div>
                        <div class="step-separator"></div>
                        <div class="step" data-step="2">
                            <span class="step-number">2</span>
                            <span class="step-label">Datos</span>
                        </div>
                        <div class="step-separator"></div>
                        <div class="step" data-step="3">
                            <span class="step-number">3</span>
                            <span class="step-label">Ruta</span>
                        </div>
                        <div class="step-separator"></div>
                        <div class="step" data-step="4">
                            <span class="step-number">4</span>
                            <span class="step-label">Confirmar</span>
                        </div>
                    </div>
                    
                    <!-- Step 1: PDF Preview -->
                    <div class="step-content" id="step1-content">
                        <h3>Vista Previa del Documento</h3>
                        <div class="pdf-preview-container">
                            <pre id="pdfTextPreview" class="code-preview"></pre>
                        </div>
                    </div>
                    
                    <!-- Step 2: Edit Data -->
                    <div class="step-content hidden" id="step2-content">
                        <h3>Editar Datos Extraídos</h3>
                        <form id="dataEditorForm" class="document-form">
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="clientName">Cliente *</label>
                                    <input type="text" id="clientName" required 
                                           placeholder="Nombre completo del cliente">
                                    <small class="form-hint">Validado contra expedientes existentes</small>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group flex-2">
                                    <label for="docType">Tipo de Documento *</label>
                                    <select id="docType" required>
                                        <option value="">Seleccionar...</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label for="docDate">Fecha Documento *</label>
                                    <input type="date" id="docDate" required>
                                </div>
                            </div>
                            
                            <div class="form-row" id="customTypeRow" style="display: none;">
                                <div class="form-group">
                                    <label for="customDocType">Especificar Tipo</label>
                                    <input type="text" id="customDocType" 
                                           placeholder="Escribir tipo de documento...">
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="expedient">Nº Expediente</label>
                                    <input type="text" id="expedient" placeholder="123/2022">
                                </div>
                                <div class="form-group flex-2">
                                    <label for="court">Juzgado</label>
                                    <input type="text" id="court" 
                                           placeholder="Juzgado de Instrucción nº...">
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="docYear">Año del Asunto</label>
                                    <input type="number" id="docYear" min="2020" max="2030" 
                                           placeholder="2026">
                                    <small class="form-hint">Año cuando se abrió el caso (no confundir con fecha del documento)</small>
                                </div>
                                <div class="form-group">
                                    <div class="confidence-badge">
                                        <span>Confianza IA:</span>
                                        <strong id="confidenceLevel">--</strong>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    
                    <!-- Step 3: Path Selector -->
                    <div class="step-content hidden" id="step3-content">
                        <h3>Seleccionar Carpeta Destino</h3>
                        <div class="path-selector">
                            <div class="folder-browser">
                                <div id="folderTree" class="folder-tree">
                                    <div class="loading-spinner">Cargando carpetas...</div>
                                </div>
                            </div>
                            <div class="selected-path-display">
                                <label>Ruta seleccionada:</label>
                                <input type="text" id="selectedPathInput" readonly 
                                       placeholder="Selecciona una carpeta arriba">
                                <button type="button" id="createNewFolderBtn" class="button-secondary">
                                    📁 Crear Nueva Carpeta
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Step 4: Final Confirmation -->
                    <div class="step-content hidden" id="step4-content">
                        <h3>✅ Confirmar Guardado</h3>
                        <div class="confirmation-summary">
                            <div class="summary-card">
                                <div class="summary-item">
                                    <span class="label">Cliente:</span>
                                    <strong id="summaryClient">--</strong>
                                </div>
                                <div class="summary-item">
                                    <span class="label">Tipo Documento:</span>
                                    <strong id="summaryType">--</strong>
                                </div>
                                <div class="summary-item">
                                    <span class="label">Fecha:</span>
                                    <strong id="summaryDate">--</strong>
                                </div>
                                <div class="summary-item">
                                    <span class="label">Expediente:</span>
                                    <strong id="summaryExpedient">--</strong>
                                </div>
                                <div class="summary-item">
                                    <span class="label">Juzgado:</span>
                                    <strong id="summaryC ourt">--</strong>
                                </div>
                                <div class="summary-item">
                                    <span class="label">Ruta Destino:</span>
                                    <strong id="summaryPath">--</strong>
                                </div>
                                <div class="summary-item">
                                    <span class="label">Nombre Archivo:</span>
                                    <strong id="summaryFilename">--</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Footer Buttons -->
                    <div class="modal-footer">
                        <button id="btnCancel" class="button-secondary" onclick="documentModal.close()">
                            Cancelar
                        </button>
                        <button id="btnPrevious" class="button-secondary" onclick="documentModal.previousStep()" 
                                style="display: none;">
                            ← Anterior
                        </button>
                        <button id="btnNext" class="button" onclick="documentModal.nextStep()">
                            Siguiente →
                        </button>
                        <button id="btnConfirm" class="button-primary" onclick="documentModal.confirmSave()" 
                                style="display: none;">
                            💾 Guardar Documento
                        </button>
                        <div id="savingSpinner" class="spinner hidden">Guardando...</div>
                    </div>
                </div>
            </div>
        `;

        // Añadir al DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    attachEventListeners() {
        // Cambio de tipo de documento
        const docTypeSelect = document.getElementById('docType');
        if (docTypeSelect) {
            docTypeSelect.addEventListener('change', (e) => {
                const customRow = document.getElementById('customTypeRow');
                if (e.target.value === 'Otro') {
                    customRow.style.display = 'block';
                } else {
                    customRow.style.display = 'none';
                }
            });
        }
    }

    async open(tempFilePath, extractedData = null, textPreview = '') {
        this.tempFilePath = tempFilePath;
        this.textPreview = textPreview;
        this.extractedData = extractedData || {};
        this.currentStep = 1;

        // Si no hay datos extraídos, llamar a propose-save
        if (!extractedData) {
            await this.proposeDocument();
        } else {
            this.editedData = { ...extractedData };
        }

        // Cargar tipos de documentos
        await this.loadDocumentTypes();

        // Mostrar modal
        const modal = document.getElementById('documentConfirmModal');
        modal.classList.remove('hidden');

        // Mostrar paso 1
        this.showStep(1);

        // Mostrar preview de texto
        this.showTextPreview();
    }

    async proposeDocument() {
        try {
            const response = await authenticatedFetch('/api/document/propose-save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    temp_file_path: this.tempFilePath,
                    hint_year: new Date().getFullYear()
                })
            });

            const data = await response.json();

            if (data.success && data.proposal) {
                this.extractedData = data.proposal;
                this.editedData = { ...data.proposal };
                this.pathOptions = data.proposal.path_options || [];
                this.textPreview = data.text_preview || '';
            } else {
                alert('Error al analizar documento: ' + (data.error || 'Error desconocido'));
                this.close();
            }
        } catch (error) {
            console.error('Error en propose-save:', error);
            alert('Error al procesar documento');
            this.close();
        }
    }

    async loadDocumentTypes() {
        try {
            const response = await fetch('/api/document/types');
            const data = await response.json();

            if (data.success && data.types) {
                const select = document.getElementById('docType');
                select.innerHTML = '<option value="">Seleccionar...</option>';

                data.types.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error cargando tipos:', error);
        }
    }

    showTextPreview() {
        const previewContainer = document.querySelector('.pdf-preview-container');
        if (!previewContainer) return;

        // Estructura para v2.2.0: Thumbnails + Dual Preview
        previewContainer.innerHTML = `
            <div class="pdf-enhanced-preview">
                <div id="thumbnailStrip" class="thumbnail-strip">
                    <div class="loading-thumbs">🔄 Cargando miniaturas...</div>
                </div>
                <div class="pdf-dual-preview">
                    <div class="pdf-image-preview">
                        <h4>Vista PDF - Página <span id="currentPageNum">1</span></h4>
                        <div id="pdfImageContainer" class="pdf-image-container">
                            <div class="loading-preview">🔄 Generando vista...</div>
                        </div>
                    </div>
                    <div class="pdf-text-preview">
                        <h4>Texto Extraído (OCR)</h4>
                        <pre id="pdfTextPreview" class="code-preview"></pre>
                    </div>
                </div>
            </div>
        `;

        this.loadThumbnails();
        this.generatePDFImage(1);

        const previewEl = document.getElementById('pdfTextPreview');
        if (previewEl && this.textPreview) {
            const lines = this.textPreview.split('\n').slice(0, 50);
            previewEl.textContent = lines.join('\n');
            if (this.textPreview.split('\n').length > 50) {
                previewEl.textContent += '\n\n... (texto truncado)';
            }
        }
    }

    async loadThumbnails() {
        try {
            const strip = document.getElementById('thumbnailStrip');
            if (!this.tempFilePath) return;

            const response = await authenticatedFetch('/api/document/thumbnails', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ temp_file_path: this.tempFilePath })
            });
            const data = await response.json();

            if (data.success && data.thumbnails) {
                strip.innerHTML = data.thumbnails.map(thumb => `
                    <div class="thumbnail-item ${thumb.page === 1 ? 'active' : ''}" 
                         data-page="${thumb.page}"
                         onclick="window.documentModal.goToPage(${thumb.page})">
                        <img src="${thumb.image}" alt="Pág ${thumb.page}">
                        <span class="thumbnail-page">Pág. ${thumb.page}</span>
                    </div>
                `).join('');
            } else {
                strip.innerHTML = '<p class="preview-error">⚠️ Error al cargar miniaturas</p>';
            }
        } catch (error) {
            console.error('Error thumbnails:', error);
        }
    }

    async goToPage(pageNum) {
        document.querySelectorAll('.thumbnail-item').forEach(item => {
            item.classList.toggle('active', parseInt(item.dataset.page) === pageNum);
        });
        document.getElementById('currentPageNum').textContent = pageNum;
        await this.generatePDFImage(pageNum);
    }

    async generatePDFImage(page = 1) {
        try {
            const container = document.getElementById('pdfImageContainer');
            if (!this.tempFilePath || !container) return;

            const response = await authenticatedFetch('/api/document/preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ temp_file_path: this.tempFilePath, page: page })
            });
            const data = await response.json();

            if (data.success && data.image) {
                container.innerHTML = `
                    <img src="${data.image}" class="pdf-preview-image" style="max-width:100%; border-radius:4px;">
                    <p class="preview-info">Página ${page} de ${data.total_pages}</p>
                `;
            } else {
                container.innerHTML = '<p class="error">⚠️ No se pudo cargar la imagen</p>';
            }
        } catch (e) {
            console.error('Error preview:', e);
        }
    }

    showStep(stepNumber) {
        this.currentStep = stepNumber;

        // Actualizar indicadores de progreso
        document.querySelectorAll('.progress-steps .step').forEach((step, index) => {
            if (index + 1 < stepNumber) {
                step.classList.add('completed');
                step.classList.remove('active');
            } else if (index + 1 === stepNumber) {
                step.classList.add('active');
                step.classList.remove('completed');
            } else {
                step.classList.remove('active', 'completed');
            }
        });

        // Mostrar/ocultar contenido de pasos
        for (let i = 1; i <= this.totalSteps; i++) {
            const content = document.getElementById(`step${i}-content`);
            if (content) {
                if (i === stepNumber) {
                    content.classList.remove('hidden');

                    // Cargar datos según el paso
                    if (i === 2) this.loadDataEditor();
                    if (i === 3) this.loadPathSelector();
                    if (i === 4) this.loadConfirmation();
                } else {
                    content.classList.add('hidden');
                }
            }
        }

        // Actualizar botones
        this.updateButtons();
    }

    loadDataEditor() {
        // Poblar formulario con datos extraídos
        document.getElementById('clientName').value = this.editedData.client || '';
        document.getElementById('docType').value = this.editedData.doc_type || '';

        // Convertir fecha de DD/MM/YYYY a YYYY-MM-DD para input type="date"
        if (this.editedData.date) {
            const parts = this.editedData.date.split('/');
            if (parts.length === 3) {
                document.getElementById('docDate').value = `${parts[2]}-${parts[1]}-${parts[0]}`;
            }
        }

        document.getElementById('expedient').value = this.editedData.expedient || '';
        document.getElementById('court').value = this.editedData.court || '';
        document.getElementById('docYear').value = this.editedData.suggested_year || new Date().getFullYear();
        document.getElementById('confidenceLevel').textContent = (this.editedData.confidence || 0) + '%';
    }

    async loadPathSelector() {
        const year = document.getElementById('docYear').value || new Date().getFullYear();
        const client = document.getElementById('clientName').value;

        try {
            const response = await authenticatedFetch(`/api/document/path-options?year=${year}&client=${encodeURIComponent(client)}`);
            const data = await response.json();

            if (data.success && data.folders) {
                this.pathOptions = data.folders;
                this.renderFolderTree();
            }
        } catch (error) {
            console.error('Error cargando carpetas:', error);
        }
    }

    renderFolderTree() {
        const tree = document.getElementById('folderTree');
        tree.innerHTML = '';

        if (this.pathOptions.length === 0) {
            tree.innerHTML = '<p class="no-folders">No hay carpetas existentes. Se creará una nueva.</p>';
            // Usar primera opción del proposal
            if (this.editedData.suggested_path) {
                this.selectedPath = this.editedData.suggested_path;
                document.getElementById('selectedPathInput').value = this.editedData.suggested_path;
            }
            return;
        }

        this.pathOptions.forEach((folder, index) => {
            const folderDiv = document.createElement('div');
            folderDiv.className = 'folder-item';
            if (index === 0) folderDiv.classList.add('selected');

            folderDiv.innerHTML = `
                <div class="folder-icon">📁</div>
                <div class="folder-info">
                    <div class="folder-name">${folder.display}</div>
                    <div class="folder-meta">${folder.document_count} documentos${folder.is_new ? ' (Nueva)' : ''}</div>
                </div>
            `;

            folderDiv.addEventListener('click', () => {
                document.querySelectorAll('.folder-item').forEach(el => el.classList.remove('selected'));
                folderDiv.classList.add('selected');
                this.selectedPath = folder.path;
                document.getElementById('selectedPathInput').value = folder.path;
            });

            tree.appendChild(folderDiv);
        });

        // Seleccionar primera por defecto
        if (this.pathOptions.length > 0) {
            this.selectedPath = this.pathOptions[0].path;
            document.getElementById('selectedPathInput').value = this.pathOptions[0].path;
        }
    }

    loadConfirmation() {
        // Recoger datos del formulario
        const clientName = document.getElementById('clientName').value;
        const docType = document.getElementById('docType').value === 'Otro'
            ? document.getElementById('customDocType').value
            : document.getElementById('docType').value;
        const docDate = document.getElementById('docDate').value;
        const expedient = document.getElementById('expedient').value;
        const court = document.getElementById('court').value;
        const year = document.getElementById('docYear').value;

        // Generar nombre de archivo
        const typeSlug = docType.toLowerCase()
            .replace(/[^a-z0-9]/g, '_')
            .replace(/_+/g, '_')
            .substring(0, 30);
        const filename = `${docDate}_${typeSlug}.pdf`;

        // Actualizar resumen
        document.getElementById('summaryClient').textContent = clientName;
        document.getElementById('summaryType').textContent = docType;
        document.getElementById('summaryDate').textContent = docDate;
        document.getElementById('summaryExpedient').textContent = expedient || '(ninguno)';
        document.getElementById('summaryCourt').textContent = court || '(ninguno)';
        document.getElementById('summaryPath').textContent = this.selectedPath || '(no seleccionada)';
        document.getElementById('summaryFilename').textContent = filename;

        // Guardar para enviar
        this.editedData = {
            client: clientName,
            doc_type: docType,
            date: docDate,
            expedient: expedient,
            court: court,
            year: parseInt(year),
            path: this.selectedPath,
            filename: filename
        };
    }

    updateButtons() {
        const btnPrevious = document.getElementById('btnPrevious');
        const btnNext = document.getElementById('btnNext');
        const btnConfirm = document.getElementById('btnConfirm');

        // Botón anterior
        if (this.currentStep > 1) {
            btnPrevious.style.display = 'inline-block';
        } else {
            btnPrevious.style.display = 'none';
        }

        // Botón siguiente/confirmar
        if (this.currentStep < this.totalSteps) {
            btnNext.style.display = 'inline-block';
            btnConfirm.style.display = 'none';
        } else {
            btnNext.style.display = 'none';
            btnConfirm.style.display = 'inline-block';
        }
    }

    nextStep() {
        // Validar paso actual antes de avanzar
        if (!this.validateCurrentStep()) {
            return;
        }

        if (this.currentStep < this.totalSteps) {
            this.showStep(this.currentStep + 1);
        }
    }

    previousStep() {
        if (this.currentStep > 1) {
            this.showStep(this.currentStep - 1);
        }
    }

    validateCurrentStep() {
        if (this.currentStep === 2) {
            // Validar formulario de datos
            const form = document.getElementById('dataEditorForm');
            if (!form.checkValidity()) {
                form.reportValidity();
                return false;
            }

            const clientName = document.getElementById('clientName').value.trim();
            const docType = document.getElementById('docType').value;
            const docDate = document.getElementById('docDate').value;

            if (!clientName || !docType || !docDate) {
                alert('Por favor completa todos los campos requeridos');
                return false;
            }

            if (docType === 'Otro' && !document.getElementById('customDocType').value.trim()) {
                alert('Por favor especifica el tipo de documento');
                return false;
            }
        }

        if (this.currentStep === 3) {
            // Validar que se haya seleccionado una ruta
            if (!this.selectedPath) {
                alert('Por favor selecciona una carpeta destino');
                return false;
            }
        }

        return true;
    }

    async confirmSave() {
        const spinner = document.getElementById('savingSpinner');
        const btnConfirm = document.getElementById('btnConfirm');

        try {
            spinner.classList.remove('hidden');
            btnConfirm.disabled = true;

            const response = await authenticatedFetch('/api/document/confirm-save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    temp_file_path: this.tempFilePath,
                    confirmed_data: this.editedData
                })
            });

            const data = await response.json();

            if (data.success) {
                alert('✅ Documento guardado correctamente en:\n' + data.final_path);
                this.close();

                // Refrescar dashboard
                if (typeof refreshDashboard === 'function') {
                    refreshDashboard();
                }
            } else {
                alert('❌ Error al guardar: ' + (data.error || 'Error desconocido'));
            }
        } catch (error) {
            console.error('Error guardando documento:', error);
            alert('❌ Error al guardar documento');
        } finally {
            spinner.classList.add('hidden');
            btnConfirm.disabled = false;
        }
    }

    close() {
        const modal = document.getElementById('documentConfirmModal');
        if (modal) {
            modal.classList.add('hidden');
        }

        // Reset
        this.currentStep = 1;
        this.tempFilePath = null;
        this.extractedData = {};
        this.editedData = {};
        this.selectedPath = null;
    }
}

// Instancia global
const documentModal = new DocumentConfirmModal();
