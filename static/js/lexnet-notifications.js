/**
 * LexNET Notifications Badge
 * Muestra contador de notificaciones urgentes en dashboard
 */

class LexNetBadge {
    constructor() {
        this.updateInterval = 60000; // 60 segundos
        this.urgentCount = 0;
        this.init();
    }

    init() {
        // Crear badge en nav item si existe
        const lexnetNavItem = document.getElementById('lexnetNavItem');
        if (lexnetNavItem) {
            this.createBadgeElement(lexnetNavItem);
        }

        // Primera actualización
        this.updateBadge();

        // Polling cada minuto
        setInterval(() => this.updateBadge(), this.updateInterval);
    }

    createBadgeElement(parentElement) {
        // Crear contenedor de badge
        const badgeContainer = document.createElement('span');
        badgeContainer.id = 'lexnetBadgeContainer';
        badgeContainer.className = 'notification-badge-container';
        badgeContainer.innerHTML = `
            <span id="lexnetBadge" class="notification-badge hidden"></span>
        `;

        parentElement.appendChild(badgeContainer);
    }

    async updateBadge() {
        try {
            const response = await authenticatedFetch('/api/lexnet/urgent-count');
            const data = await response.json();

            if (data.success) {
                this.urgentCount = data.urgent_count;
                this.renderBadge();
            }
        } catch (error) {
            console.error('Error actualizando badge LexNET:', error);
        }
    }

    renderBadge() {
        const badge = document.getElementById('lexnetBadge');

        if (!badge) return;

        if (this.urgentCount > 0) {
            badge.textContent = this.urgentCount > 99 ? '99+' : this.urgentCount;
            badge.classList.remove('hidden');
            badge.classList.add('urgent');

            // Animar si es nuevo
            badge.classList.add('pulse');
            setTimeout(() => badge.classList.remove('pulse'), 2000);
        } else {
            badge.classList.add('hidden');
        }
    }

    async showNotificationsPanel() {
        try {
            const response = await authenticatedFetch('/api/lexnet/notifications?unread=true');
            const data = await response.json();

            if (data.success) {
                this.renderNotificationsModal(data.notifications);
            }
        } catch (error) {
            console.error('Error cargando notificaciones:', error);
        }
    }

    renderNotificationsModal(notifications) {
        // Crear modal de notificaciones
        const modalHTML = `
            <div id="notificationsModal" class="modal">
                <div class="modal-overlay" onclick="closeLexNetModal()"></div>
                <div class="modal-content notifications-modal">
                    <div class="modal-header">
                        <h2>🔔 Notificaciones LexNET</h2>
                        <button class="close-modal" onclick="closeLexNetModal()">&times;</button>
                    </div>
                    
                    <div class="notifications-list">
                        ${notifications.length > 0
                ? notifications.map(n => this.renderNotificationItem(n)).join('')
                : '<p class="no-notifications">No hay notificaciones urgentes</p>'
            }
                    </div>
                    
                    <div class="modal-footer">
                        <button class="button-secondary" onclick="closeLexNetModal()">Cerrar</button>
                    </div>
                </div>
            </div>
        `;

        // Añadir al DOM
        const existing = document.getElementById('notificationsModal');
        if (existing) existing.remove();

        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Mostrar modal
        document.getElementById('notificationsModal').classList.remove('hidden');
    }

    renderNotificationItem(notification) {
        const urgencyClass = notification.urgency.toLowerCase();
        const urgencyIcon = {
            'CRITICAL': '🔴',
            'URGENT': '🟠',
            'WARNING': '🟡',
            'NORMAL': '🟢'
        }[notification.urgency] || '⚪';

        return `
            <div class="notification-item ${urgencyClass}" data-id="${notification.id}">
                <div class="notification-icon">${urgencyIcon}</div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-meta">
                        ${notification.procedure_number ? `<span>📋 ${notification.procedure_number}</span>` : ''}
                        ${notification.deadline ? `<span>⏰ Vence: ${new Date(notification.deadline).toLocaleDateString('es-ES')}</span>` : ''}
                    </div>
                    <div class="notification-body">${notification.body.substring(0, 150)}...</div>
                    <div class="notification-days-left">
                        ${this.calculateDaysLeft(notification.deadline)}
                    </div>
                </div>
                <div class="notification-actions">
                    <button class="btn-icon" onclick="markAsRead(${notification.id})" title="Marcar como leída">
                        ✅
                    </button>
                </div>
            </div>
        `;
    }

    calculateDaysLeft(deadline) {
        if (!deadline) return '';

        const now = new Date();
        const deadlineDate = new Date(deadline);
        const daysLeft = Math.ceil((deadlineDate - now) / (1000 * 60 * 60 * 24));

        if (daysLeft < 0) {
            return `<span class="days-left expired">⚠️ VENCIDO</span>`;
        } else if (daysLeft === 0) {
            return `<span class="days-left critical">🔴 VENCE HOY</span>`;
        } else if (daysLeft === 1) {
            return `<span class="days-left critical">🔴 VENCE MAÑANA</span>`;
        } else if (daysLeft <= 2) {
            return `<span class="days-left urgent">🟠 ${daysLeft} días</span>`;
        } else if (daysLeft <= 5) {
            return `<span class="days-left warning">🟡 ${daysLeft} días</span>`;
        } else {
            return `<span class="days-left normal">🟢 ${daysLeft} días</span>`;
        }
    }
}

// Funciones globales
async function markAsRead(notificationId) {
    try {
        const response = await authenticatedFetch(`/api/lexnet/notifications/${notificationId}/read`, {
            method: 'PATCH'
        });

        const data = await response.json();

        if (data.success) {
            // Remover del DOM
            const item = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
            if (item) {
                item.style.opacity = '0.5';
                setTimeout(() => item.remove(), 300);
            }

            // Actualizar badge
            if (window.lexnetBadge) {
                window.lexnetBadge.updateBadge();
            }
        }
    } catch (error) {
        console.error('Error marcando como leída:', error);
    }
}

function closeLexNetModal() {
    const modal = document.getElementById('notificationsModal');
    if (modal) {
        modal.remove();
    }
}

function openLexNetNotifications() {
    if (window.lexnetBadge) {
        window.lexnetBadge.showNotificationsPanel();
    }
}

// Inicializar badge automáticamente
document.addEventListener('DOMContentLoaded', () => {
    window.lexnetBadge = new LexNetBadge();
});
