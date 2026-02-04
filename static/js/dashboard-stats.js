/**
 * Dashboard Stats Visualization
 * Muestra KPIs y gráficas de estadísticas del sistema
 */

class DashboardStats {
    constructor() {
        this.chart = null;
        this.updateInterval = 30000; // 30 segundos
        this.init();
    }

    init() {
        // Cargar primera vez
        this.updateStats();

        // Actualizar periódicamente
        setInterval(() => this.updateStats(), this.updateInterval);
    }

    async updateStats() {
        try {
            const response = await authenticatedFetch('/api/dashboard/stats-detailed');
            const data = await response.json();

            if (data.success) {
                this.renderKPIs(data.stats);
                this.renderChart(data.stats.trend_data);
                this.renderTopLists(data.stats);
                this.renderRecentDocuments(data.stats.recent_documents);
            }
        } catch (error) {
            console.error('Error actualizando stats:', error);
        }
    }

    renderKPIs(stats) {
        // Actualizar contadores principales
        const kpis = [
            { id: 'kpiToday', value: stats.today, label: 'Hoy' },
            { id: 'kpiWeek', value: stats.week, label: 'Esta Semana' },
            { id: 'kpiMonth', value: stats.month, label: 'Este Mes' },
            { id: 'kpiTotal', value: stats.total, label: 'Total' }
        ];

        kpis.forEach(kpi => {
            const el = document.getElementById(kpi.id);
            if (el) {
                el.textContent = kpi.value;
            }
        });

        // Notificaciones urgentes
        const urgentEl = document.getElementById('kpiUrgent');
        if (urgentEl && stats.urgent_notifications > 0) {
            urgentEl.textContent = stats.urgent_notifications;
            urgentEl.classList.add('urgent');
        }
    }

    renderChart(trendData) {
        const canvas = document.getElementById('trendChart');

        if (!canvas) return;

        // Destruir chart anterior si existe
        if (this.chart) {
            this.chart.destroy();
        }

        // Crear nuevo chart
        const ctx = canvas.getContext('2d');

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: trendData.labels,
                datasets: [{
                    label: 'Documentos Procesados',
                    data: trendData.values,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#3b82f6',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#1f2937',
                        padding: 12,
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#3b82f6',
                        borderWidth: 1
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            color: '#6b7280'
                        },
                        grid: {
                            color: '#e5e7eb'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#6b7280'
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    renderTopLists(stats) {
        // Top tipos de documento
        const typesList = document.getElementById('topTypesList');
        if (typesList && stats.by_type) {
            typesList.innerHTML = Object.entries(stats.by_type)
                .slice(0, 5)
                .map(([type, count]) => `
                    <div class="top-item">
                        <span class="top-label">${type}</span>
                        <span class="top-count">${count}</span>
                    </div>
                `).join('');
        }

        // Top clientes
        const clientsList = document.getElementById('topClientsList');
        if (clientsList && stats.by_client) {
            clientsList.innerHTML = Object.entries(stats.by_client)
                .slice(0, 5)
                .map(([client, count]) => `
                    <div class="top-item">
                        <span class="top-label">${client}</span>
                        <span class="top-count">${count}</span>
                    </div>
                `).join('');
        }
    }

    renderRecentDocuments(documents) {
        const list = document.getElementById('recentDocumentsList');

        if (!list || !documents) return;

        list.innerHTML = documents.map(doc => `
            <div class="recent-doc-item">
                <div class="recent-doc-icon">📄</div>
                <div class="recent-doc-info">
                    <div class="recent-doc-name">${doc.filename}</div>
                    <div class="recent-doc-meta">
                        <span>${doc.client || 'Sin cliente'}</span>
                        <span>•</span>
                        <span>${doc.type || 'Sin tipo'}</span>
                        <span>•</span>
                        <span>${this.formatDate(doc.created_at)}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async exportToPDF() {
        const btn = document.getElementById('btnExportPDF');
        const originalText = btn.innerHTML;

        try {
            btn.disabled = true;
            btn.innerHTML = '⏳ Generando...';

            const response = await authenticatedFetch('/api/dashboard/export-pdf');
            if (!response.ok) throw new Error('Error al generar PDF');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `reporte_dashboard_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);

            btn.innerHTML = '✅ Completado';
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }, 2000);

        } catch (error) {
            console.error('Error exportando PDF:', error);
            btn.innerHTML = '❌ Error';
            btn.classList.add('button-danger');
            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
                btn.classList.remove('button-danger');
            }, 3000);
        }
    }

    formatDate(dateString) {
        if (!dateString) return '';

        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Ahora mismo';
        if (diffMins < 60) return `Hace ${diffMins}m`;
        if (diffHours < 24) return `Hace ${diffHours}h`;
        if (diffDays < 7) return `Hace ${diffDays}d`;

        return date.toLocaleDateString('es-ES', {
            day: '2-digit',
            month: 'short'
        });
    }
}

// Inicializar automáticamente si existe el contenedor
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('trendChart')) {
        window.dashboardStats = new DashboardStats();
    }
});
