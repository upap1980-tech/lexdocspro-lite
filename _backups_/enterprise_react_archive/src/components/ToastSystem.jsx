import React, { useState, useEffect } from 'react';
import { AlertTriangle, X, ArrowRight } from 'lucide-react';

const Toast = ({ id, message, value, onClose }) => {
    useEffect(() => {
        const timer = setTimeout(() => onClose(id), 10000);
        return () => clearTimeout(timer);
    }, [id, onClose]);

    return (
        <div className="bg-industrial-card border-l-4 border-industrial-danger p-4 rounded-xl shadow-2xl flex items-start gap-4 animate-slide-in mb-3 max-w-sm border border-slate-800">
            <div className="bg-industrial-danger/10 p-2 rounded-lg text-industrial-danger flex-shrink-0">
                <AlertTriangle size={18} />
            </div>
            <div className="flex-1 min-w-0">
                <h4 className="text-sm font-bold text-white mb-1">Alerta Modelo 347</h4>
                <p className="text-xs text-slate-400 leading-snug truncate">{message}</p>
                <p className="text-[10px] font-mono font-bold text-industrial-danger mt-1 uppercase">Importe: {value}€</p>
            </div>
            <button onClick={() => onClose(id)} className="text-slate-500 hover:text-white transition-colors">
                <X size={16} />
            </button>
        </div>
    );
};

const ToastSystem = () => {
    const [toasts, setToasts] = useState([
        { id: 1, message: 'Factura López S.L. ha superado el umbral fiscal.', value: '15,400.00' },
        { id: 2, message: 'Posible declaración informativa requerida para BBVA.', value: '8,250.00' }
    ]);

    const removeToast = (id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    };

    return (
        <div className="fixed top-20 right-8 z-[200] flex flex-col items-end">
            {toasts.map(toast => (
                <Toast key={toast.id} {...toast} onClose={removeToast} />
            ))}

            {toasts.length > 0 && (
                <button className="bg-industrial-dark border border-slate-800 px-3 py-1.5 rounded-full text-[10px] font-bold text-slate-400 hover:text-white transition-all flex items-center gap-2 group mt-2">
                    Ver todas las alertas <ArrowRight size={12} className="group-hover:translate-x-1 transition-transform" />
                </button>
            )}
        </div>
    );
};

export default ToastSystem;
