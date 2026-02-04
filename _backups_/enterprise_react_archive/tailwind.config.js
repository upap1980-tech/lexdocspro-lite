/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                industrial: {
                    dark: '#0A0F1E',
                    card: '#1E293B',
                    accent: '#3B82F6',
                    alert: '#F59E0B',
                    success: '#10B981',
                    danger: '#EF4444'
                }
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                mono: ['Inter Mono', 'monospace'],
            },
        },
    },
    plugins: [],
}
