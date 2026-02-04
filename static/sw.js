/*
 LexDocsPro Service Worker v2.2.0
 Soporte para PWA y Notificaciones Push
*/

const CACHE_NAME = 'lexdocspro-v2.2.0';
const ASSETS = [
    '/',
    '/static/css/main.css',
    '/static/js/auth.js',
    '/static/js/dashboard-stats.js'
];

// Instalación
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ASSETS))
    );
});

// Activación
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        })
    );
});

// Push Notifications
self.addEventListener('push', event => {
    let data = { title: 'Nueva Notificación', body: 'Tienes un nuevo mensaje en LexDocsPro' };

    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data.body = event.data.text();
        }
    }

    const options = {
        body: data.body,
        icon: '/static/img/icon-192.png',
        badge: '/static/img/icon-192.png',
        data: data.url || '/',
        vibrate: [100, 50, 100],
        actions: [
            { action: 'open', title: 'Ver Detalles' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Click en notificación
self.addEventListener('notificationclick', event => {
    event.notification.close();

    const url = event.notification.data || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(windowClients => {
            for (let client of windowClients) {
                if (client.url === url && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});
