<!--- Dashboard Fix v2.3.1 - Completo --->
(function() {
    'use strict';
    console.log('🎯 Dashboard Fix v2.3.1 cargado');
    
    // Export PDF - Universal
    document.addEventListener('click', function(e) {
        const target = e.target.closest('button, a');
        if (!target) return;
        
        const text = target.textContent.toLowerCase();
        if (text.includes('pdf') || text.includes('exportar')) {
            e.preventDefault();
            window.open('/api/dashboard/export-pdf', '_blank');
            console.log('📄 PDF exportado');
            return false;
        }
        
        if (text.includes('admin')) {
            e.preventDefault();
            window.location.hash = 'admin';
            console.log('👤 Admin abierto');
            return false;
        }
    });
    
    // Limpiar "En Revisión"
    document.querySelectorAll('[data-status="revision"], .review-count').forEach(el => {
        el.textContent = '0';
    });
    
    console.log('✅ Fix aplicado: PDF + Admin + Revisión');
})();
