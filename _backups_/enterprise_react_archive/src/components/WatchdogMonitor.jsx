import React from 'react';
import { Activity, Folder, CheckCircle, AlertCircle, RefreshCcw, Search } from 'lucide-react';

const WatchdogEvent = ({ time, file, status, type }) => {
    const getStatusColor = () => {
        switch (status) {
            case 'success': return 'text-industrial-success';
            case 'processing': return 'text-industrial-accent';
            case 'error': return 'text-industrial-danger';
            default: return 'text-slate-500';
        }
    };

    return (
        <div className="flex gap-4 p-4 hover:bg-slate-800/30 rounded-2xl transition-colors border border-transparent hover:border-slate-800/50">
            <div className="flex flex-col items-center">
                <div className={`w-2 h-2 rounded-full ${getStatusColor()} mt-1.5 shadow-[0_0_8px_currentColor]`}></div>
                <div className="w-[1px] flex-1 bg-slate-800 mt-2"></div>
            </div>
            <div className="flex-1">
                <div className="flex justify-between items-start mb-1">
                    <h4 className="text-xs font-bold text-slate-200 truncate max-w-[200px]">{file}</h4>
                    <span className="text-[10px] font-mono text-slate-500">{time}</span>
                </div>
                <p className="text-[11px] text-slate-400">
                    {type === 'ocr' ? 'OCR & Análisis IA completado' : 'Archivo detectado en cola de entrada'}
                </p>
            </div>
        </div>
    );
};

const WatchdogMonitor = () => {
    return (
        <div className="p-8 mt-16 ml-64 bg-industrial-dark min-h-screen">
            <div className="flex justify-between items-end mb-10">
                <div>
                    <h2 className="text-2xl font-bold text-white mb-1">Watchdog Monitor PRO</h2>
                    <p className="text-slate-500 text-sm">Supervisión en tiempo real del procesamiento automático de archivos.</p>
                </div>
                <button className="flex items-center gap-2 bg-industrial-accent/10 border border-industrial-accent/30 text-industrial-accent px-4 py-2 rounded-xl text-xs font-bold hover:bg-industrial-accent/20 transition-all">
                    <RefreshCcw size={14} className="animate-spin-slow" /> Forzar Escaneo
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-industrial-card border border-slate-800 rounded-3xl p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-white font-bold flex items-center gap-2">
                                <Activity size={18} className="text-industrial-accent" /> Timeline de Actividad (24h)
                            </h3>
                            <div className="relative">
                                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                                <input type="text" placeholder="Filtrar archivos..." className="bg-industrial-dark border border-slate-700 rounded-lg py-1.5 pl-9 pr-4 text-[10px] text-slate-300 outline-none w-48" />
                            </div>
                        </div>

                        <div className="space-y-2 h-[500px] overflow-y-auto custom-scrollbar pr-2">
                            <WatchdogEvent time="09:45" file="DEMANDA_OR_45_2024.pdf" status="success" type="ocr" />
                            <WatchdogEvent time="09:42" file="CONTRATO_ARRENDAMIENTO_V2.pdf" status="processing" type="scan" />
                            <WatchdogEvent time="09:30" file="FACTURA_LOPEZ_SL.pdf" status="success" type="ocr" />
                            <WatchdogEvent time="09:28" file="RECURSO_APELACION_FINAL.pdf" status="error" type="ocr" />
                            <WatchdogEvent time="09:12" file="CITACION_JUDICIAL_MADRID.pdf" status="success" type="scan" />
                            <WatchdogEvent time="08:55" file="DOCUMENTO_PRUEBA_001.pdf" status="success" type="ocr" />
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="bg-industrial-card border border-slate-800 p-6 rounded-3xl">
                        <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-6 px-1">Estado de Carpetas</h3>
                        <div className="space-y-4">
                            <div className="bg-slate-900/50 p-4 rounded-2xl border border-slate-800/50">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-xs font-bold text-slate-200 flex items-center gap-2"><Folder size={14} className="text-industrial-accent" /> /Entrada</span>
                                    <span className="text-[10px] font-mono text-industrial-success">ESCANEO ACTIVO</span>
                                </div>
                                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                                    <div className="bg-industrial-accent w-[65%] h-full rounded-full animate-pulse"></div>
                                </div>
                            </div>
                            <div className="bg-slate-900/50 p-4 rounded-2xl border border-slate-800/50">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-xs font-bold text-slate-200 flex items-center gap-2"><Folder size={14} className="text-slate-500" /> /Procesados</span>
                                    <span className="text-[10px] font-mono text-slate-500 text-xs">OK</span>
                                </div>
                                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                                    <div className="bg-industrial-success w-full h-full rounded-full"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-industrial-accent/20 to-slate-900 border border-industrial-accent/30 p-6 rounded-3xl">
                        <h4 className="text-white font-bold mb-2 flex items-center gap-2">
                            <CheckCircle size={16} className="text-industrial-success" /> Auto-Optimizador
                        </h4>
                        <p className="text-xs text-slate-400 leading-relaxed">
                            El sistema ha liberado 1.2GB de caché de OCR hoy. Rendimiento mejorado en un 14%.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default WatchdogMonitor;
