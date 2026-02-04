import React from 'react';
import { Power, Shield, Activity, Bell } from 'lucide-react';

const StatusBadge = ({ label, status, color }) => {
    const getDotColor = () => {
        switch (status) {
            case 'active': return 'bg-industrial-success';
            case 'standby': return 'bg-industrial-accent';
            case 'alert': return 'bg-industrial-alert';
            default: return 'bg-slate-500';
        }
    };

    return (
        <div className="flex items-center gap-2 bg-slate-900/50 px-3 py-1.5 rounded-full border border-slate-700/50">
            <div className={`w-2 h-2 rounded-full ${getDotColor()} shadow-[0_0_8px] ${color}`}></div>
            <span className="text-[11px] font-mono uppercase tracking-wider text-slate-300">{label}</span>
        </div>
    );
};

const Header = () => {
    return (
        <header className="h-16 bg-industrial-dark/80 backdrop-blur-md border-b border-slate-800 flex items-center justify-between px-8 fixed top-0 right-0 left-64 z-40">
            <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                    <div className="bg-gradient-to-br from-yellow-400 to-yellow-600 text-[10px] font-bold text-black px-2 py-0.5 rounded flex items-center gap-1 shadow-lg shadow-yellow-500/10">
                        v2.3.0 LIVE
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <StatusBadge label="Ollama" status="active" color="shadow-industrial-success/50" />
                    <StatusBadge label="Groq" status="standby" color="shadow-industrial-accent/50" />
                    <StatusBadge label="OpenAI" status="standby" color="shadow-slate-500/50" />
                </div>
            </div>

            <div className="flex items-center gap-4">
                <div className="bg-industrial-card border border-slate-700 p-2 rounded-lg cursor-pointer hover:bg-slate-700 transition-colors relative">
                    <Bell size={18} className="text-slate-300" />
                    <span className="absolute top-1 right-1 w-2 h-2 bg-industrial-danger rounded-full ring-2 ring-industrial-dark"></span>
                </div>

                <div className="flex items-center gap-3 pl-4 border-l border-slate-700">
                    <div className="text-right">
                        <p className="text-xs font-bold text-white">Abogado Corresponsal</p>
                        <p className="text-[10px] text-industrial-accent font-mono uppercase">Certificado Activo</p>
                    </div>
                    <div className="w-9 h-9 bg-industrial-accent/20 border border-industrial-accent/30 rounded-full flex items-center justify-center text-industrial-accent font-bold">
                        LC
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
