#!/usr/bin/env python3
"""
Actualizar sección IA Cascade en index.html
"""

with open('templates/index.html', 'r', encoding='utf-8') as f:
    contenido = f.read()

import re

# Reemplazar placeholder
seccion_nueva = '''        <section id="ia-cascade" class="section">
            <h1 style="margin-bottom: 30px; color: #333;">🔍 IA Cascade - Multi-Provider</h1>
            
            <!-- Panel de Test -->
            <div style="background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px;">
                <h3>Test de Query</h3>
                
                <textarea id="ia-prompt" style="width: 100%; height: 120px; padding: 15px; border: 1px solid #ddd; border-radius: 6px; font-family: monospace; margin: 15px 0;" placeholder="Escribe tu prompt aquí..."></textarea>
                
                <button onclick="testIACascade()" style="padding: 10px 30px; background: #007BFF; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">
                    🚀 EJECUTAR QUERY
                </button>
                
                <div id="ia-response" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 6px; min-height: 100px; font-family: monospace; display: none;">
                    <strong>Respuesta:</strong>
                    <div id="ia-response-text" style="margin-top: 10px; white-space: pre-wrap;"></div>
                </div>
            </div>
            
            <!-- Providers -->
            <h3 style="margin: 30px 0 15px 0;">Providers Disponibles</h3>
            <div id="ia-providers" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
                <p style="color: #999; padding: 40px; text-align: center;">Cargando providers...</p>
            </div>
            
            <!-- Estadísticas Globales -->
            <div class="kpi-grid" style="margin-top: 30px;">
                <div class="kpi-card success">
                    <h3>Total Queries</h3>
                    <span class="kpi-value" id="ia-total">0</span>
                </div>
                <div class="kpi-card info">
                    <h3>Exitosas</h3>
                    <span class="kpi-value" id="ia-success">0</span>
                </div>
                <div class="kpi-card danger">
                    <h3>Fallidas</h3>
                    <span class="kpi-value" id="ia-failed">0</span>
                </div>
            </div>
        </section>'''

contenido = re.sub(
    r'<section id="ia-cascade" class="section">.*?</section>',
    seccion_nueva,
    contenido,
    flags=re.DOTALL
)

# Añadir JavaScript
js_nuevo = '''
        // IA CASCADE FUNCTIONS
        function loadIACascadeStatus() {
            fetch('/api/ia-cascade/status')
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        const status = data.status;
                        
                        // Stats globales
                        document.getElementById('ia-total').textContent = status.global_stats.total_requests;
                        document.getElementById('ia-success').textContent = status.global_stats.successful;
                        document.getElementById('ia-failed').textContent = status.global_stats.failed;
                        
                        // Providers
                        const providersHTML = status.providers.map(p => `
                            <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid ${p.available ? '#28a745' : '#dc3545'};">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong style="font-size: 1.1rem;">${p.name}</strong>
                                        <div style="color: #666; font-size: 0.9rem; margin-top: 5px;">${p.model}</div>
                                        <div style="color: #999; font-size: 0.8rem;">Prioridad: ${p.priority}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-size: 1.5rem;">${p.available ? '🟢' : '🔴'}</div>
                                        <div style="font-size: 0.8rem; color: #666; margin-top: 5px;">
                                            ${p.stats.success} / ${p.stats.requests}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('');
                        
                        document.getElementById('ia-providers').innerHTML = providersHTML;
                    }
                })
                .catch(e => console.error(e));
        }
        
        function testIACascade() {
            const prompt = document.getElementById('ia-prompt').value;
            if (!prompt.trim()) {
                alert('Escribe un prompt primero');
                return;
            }
            
            document.getElementById('ia-response').style.display = 'block';
            document.getElementById('ia-response-text').textContent = '⏳ Procesando...';
            
            fetch('/api/ia-cascade/query', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: prompt})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('ia-response-text').textContent = 
                        `[${data.provider} - ${data.model}]\n\n${data.response}`;
                    loadIACascadeStatus();
                } else {
                    document.getElementById('ia-response-text').textContent = 
                        `❌ Error: ${data.error}`;
                }
            })
            .catch(e => {
                document.getElementById('ia-response-text').textContent = 
                    `❌ Error: ${e.message}`;
            });
        }
        
        // Cargar al abrir tab
        const origShowTab2 = window.showTab;
        window.showTab = function(tab) {
            origShowTab2(tab);
            if (tab === 'ia-cascade') {
                loadIACascadeStatus();
            }
        };
'''

# Insertar
partes = contenido.rsplit('</script>', 1)
if len(partes) == 2:
    contenido = partes[0] + js_nuevo + '\n    </script>' + partes[1]

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ Módulo IA Cascade actualizado en HTML")

