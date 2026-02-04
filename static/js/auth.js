/**
 * Módulo de Autenticación - Frontend
 * LexDocsPro LITE v2.0
 * Gestión de JWT tokens y estado del usuario
 */

const AuthModule = (() => {
    const AUTH_TOKEN_KEY = 'lexdocs_access_token';
    const REFRESH_TOKEN_KEY = 'lexdocs_refresh_token';
    const USER_KEY = 'lexdocs_user';
    const API_BASE = window.location.origin;

    /**
     * Guardar tokens y usuario en localStorage
     */
    function saveSession(accessToken, refreshToken, user) {
        localStorage.setItem(AUTH_TOKEN_KEY, accessToken);
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        console.log('✅ Sesión guardada:', user.email);
    }

    /**
     * Obtener token de acceso
     */
    function getAccessToken() {
        return localStorage.getItem(AUTH_TOKEN_KEY);
    }

    /**
     * Obtener refresh token
     */
    function getRefreshToken() {
        return localStorage.getItem(REFRESH_TOKEN_KEY);
    }

    /**
     * Obtener usuario actual
     */
    function getCurrentUser() {
        const userStr = localStorage.getItem(USER_KEY);
        return userStr ? JSON.parse(userStr) : null;
    }

    /**
     * Verificar si hay sesión activa
     */
    function isAuthenticated() {
        return !!getAccessToken() && !!getCurrentUser();
    }

    /**
     * Cerrar sesión (limpiar localStorage)
     */
    function clearSession() {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        console.log('🔓 Sesión cerrada');
    }

    /**
     * Login
     */
    async function login(email, password) {
        try {
            const response = await fetch(`${API_BASE}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                saveSession(data.access_token, data.refresh_token, data.user);
                return { success: true, user: data.user };
            } else {
                return { success: false, error: data.error || 'Error de autenticación' };
            }
        } catch (error) {
            console.error('Error en login:', error);
            return { success: false, error: 'Error de conexión' };
        }
    }

    /**
     * Logout
     */
    async function logout() {
        try {
            const token = getAccessToken();
            if (token) {
                await fetch(`${API_BASE}/api/auth/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
            }
        } catch (error) {
            console.error('Error en logout:', error);
        } finally {
            clearSession();
            window.location.href = '/';
        }
    }

    /**
     * Refrescar token de acceso
     */
    async function refreshAccessToken() {
        try {
            const refreshToken = getRefreshToken();
            if (!refreshToken) {
                throw new Error('No refresh token');
            }

            const response = await fetch(`${API_BASE}/api/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${refreshToken}`
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
                return data.access_token;
            } else {
                // Refresh token expirado, cerrar sesión
                clearSession();
                window.location.href = '/';
                return null;
            }
        } catch (error) {
            console.error('Error refrescando token:', error);
            clearSession();
            window.location.href = '/';
            return null;
        }
    }

    /**
     * Hacer petición autenticada (con auto-refresh)
     */
    async function authenticatedFetch(url, options = {}) {
        let token = getAccessToken();

        if (!token) {
            throw new Error('No autenticado');
        }

        // Añadir header de autorización
        options.headers = {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        };

        let response = await fetch(url, options);

        // Si token expiró (401), intentar refresh
        if (response.status === 401) {
            console.log('⚠️ Token expirado, refrescando...');
            token = await refreshAccessToken();

            if (!token) {
                throw new Error('Sesión expirada');
            }

            // Reintentar con nuevo token
            options.headers['Authorization'] = `Bearer ${token}`;
            response = await fetch(url, options);
        }

        return response;
    }

    /**
     * Obtener información del usuario actual (whoami)
     */
    async function whoami() {
        try {
            const response = await authenticatedFetch(`${API_BASE}/api/auth/whoami`);
            const data = await response.json();

            if (response.ok && data.success) {
                // Actualizar usuario en localStorage
                localStorage.setItem(USER_KEY, JSON.stringify(data.user));
                return data.user;
            } else {
                return null;
            }
        } catch (error) {
            console.error('Error en whoami:', error);
            return null;
        }
    }

    /**
     * Verificar si usuario tiene uno de los roles requeridos
     */
    function hasRole(requiredRoles) {
        const user = getCurrentUser();
        if (!user) return false;
        return requiredRoles.includes(user.rol);
    }

    // API Pública
    return {
        login,
        logout,
        isAuthenticated,
        getCurrentUser,
        getAccessToken,
        refreshAccessToken,
        authenticatedFetch,
        whoami,
        hasRole,
        clearSession
    };
})();

// Hacer disponible globalmente
window.AuthModule = AuthModule;
