import React from 'react';
import { Activity, Cpu, Shield, AlertTriangle, ArrowUpRight, Clock } from 'lucide-react';

const StatusCard = ({ title, value, subtext, icon: Icon, trend, color, status }) => (
    <div className="bg-industrial-card border border-slate-800 p-5 rounded-2xl hover:border-industrial-accent/50 transition-all duration-300 group">
        <div className="flex justify-between items-start mb-4">
            <div className={`p-2.5 rounded-xl bg-industrial-dark border border-slate-700/50 text-${color}`}>
                <Icon size={22} />
            </div>
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-slate-900/50 border border-slate-800">
                <div className={`w-1.5 h-1.5 rounded-full bg-${status} animate-pulse`}></div>
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-tighter">Live</span>
            </div>
        </div>

        <div className="space-y-1">
            <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider">{title}</h3>
            <div className="flex items-end gap-2">
                <span className="text-2xl font-bold text-white leading-none">{value}</span>
                {trend && (
                    <span className="text-industrial-success text-[10px] font-bold flex items-center mb-1">
                        <ArrowUpRight size={10} /> {trend}
                    </span>
                )}
            </div>
            <p className="text-slate-500 text-[11px] flex items-center gap-1">
                <Clock size={10} /> {subtext}
            </p>
        </div>
    </div>
);

const Dashboard = () => {
    return (
        <div className="p-8 mt-16 ml-64 bg-industrial-dark min-h-screen">
            <div className="mb-10">
                <h2 className="text-2xl font-bold text-white mb-1">Panel de Control Industrial</h2>
                <p className="text-slate-500 text-sm">Monitoreo de sistemas IA y cumplimiento legal en tiempo real.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
                <StatusCard
                    title="Watchdog LIVE"
                    value="1,247"
                    subtext="Último escaneo: hace 2m"
                    icon={Activity}
                    trend="+12%"
                    color="industrial-accent"
                    status="industrial-success"
                />
                <StatusCard
                    title="AI Agent v3"
                    value="238"
                    subtext="Historial de contexto activo"
                    icon={Cpu}
                    trend="+5%"
                    color="industrial-accent"
                    status="industrial-success"
                />
                <StatusCard
                    title="Modelo 347"
                    value="14"
                    subtext="Alertas > 3.005,06€ hoy"
                    icon={AlertTriangle}
                    color="industrial-alert"
                    status="industrial-danger"
                />
                <StatusCard
                    title="Firma PAdES"
                    value="5"
                    subtext="Pendientes de validación"
                    icon={Shield}
                    color="industrial-accent"
                    status="industrial-alert"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-industrial-card border border-slate-800 rounded-2xl p-6 h-80 flex flex-col">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-white font-bold">Actividad de la Cascada IA</h3>
                        <div className="flex items-center gap-4 text-[10px] font-mono uppercase text-slate-500">
                            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-industrial-success"></div> Ollama</span>
                            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-industrial-accent"></div> Groq</span>
                            <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-slate-600"></div> OpenAI</span>
                        </div>
                    </div>
                    <div className="flex-1 flex items-end gap-3 pb-2 px-4">
                        {/* Simulación de gráfico de barras minimalista */}
                        {[40, 60, 45, 80, 55, 70, 90, 65, 50, 75, 85, 60].map((h, i) => (
                            <div key={i} className="flex-1 group relative">
                                <div
                                    className="w-full bg-industrial-accent/20 rounded-t-sm transition-all duration-500 group-hover:bg-industrial-accent"
                                    style={{ height: `${h}%` }}
                                ></div>
                                <div className="absolute -top-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap text-[9px] font-mono bg-slate-800 text-white px-1 rounded">
                                    {h} docs
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-industrial-card border border-slate-800 rounded-2xl p-6 flex flex-col">
                    <h3 className="text-white font-bold mb-6">Logs de sistema</h3>
                    <div className="space-y-4 font-mono text-[10px] overflow-y-auto max-h-60 pr-2 custom-scrollbar">
                        <div className="flex gap-2 text-industrial-success">
                            <span className="opacity-50">09:32:01</span>
                            <span>[OK] Documento #459 procesado (Ollama)</span>
                        </div>
                        <div className="flex gap-2 text-industrial-alert">
                            <span className="opacity-50">09:31:45</span>
                            <span>[WARN] Alerta Modelo 347 detectada</span>
                        </div>
                        <div className="flex gap-2 text-industrial-accent">
                            <span className="opacity-50">09:30:12</span>
                            <span>[INFO] Escalando peticion a Groq API...</span>
                        </div>
                        <div className="flex gap-2 text-slate-500">
                            <span className="opacity-50">09:28:55</span>
                            <span>[INFO] Watchdog: Nuevo archivo detectado</span>
                        </div>
                        <div className="flex gap-2 text-industrial-success">
                            <span className="opacity-50">09:25:33</span>
                            <span>[OK] Firma PAdES validada satisfactoriamente</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
