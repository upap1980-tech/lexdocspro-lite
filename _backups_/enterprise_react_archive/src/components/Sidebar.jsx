import React from 'react';
import { LayoutDashboard, FileText, Cpu, ShieldCheck, AlertCircle, Settings } from 'lucide-react';

const SidebarItem = ({ icon: Icon, label, active, badge, onClick }) => (
    <div
        onClick={onClick}
        className={`flex items-center justify-between p-3 mb-2 rounded-xl cursor-pointer transition-all duration-300 group ${active ? 'bg-industrial-accent text-white shadow-xl shadow-industrial-accent/20' : 'text-slate-500 hover:bg-slate-800/50 hover:text-slate-200'
            }`}>
        <div className="flex items-center gap-3">
            <div className={`transition-transform duration-300 group-hover:scale-110 ${active ? 'text-white' : 'text-slate-600'}`}>
                <Icon size={18} />
            </div>
            <span className="text-sm font-bold tracking-tight">{label}</span>
        </div>
        {badge && (
            <span className="bg-industrial-danger text-white text-[9px] px-1.5 py-0.5 rounded-md font-bold ring-2 ring-industrial-dark">
                {badge}
            </span>
        )}
    </div>
);

const Sidebar = ({ current, onNavigate }) => {
    return (
        <div className="w-64 h-screen bg-industrial-dark border-r border-slate-800/50 flex flex-col p-6 fixed left-0 top-0 z-50">
            <div className="mb-12 px-2">
                <div className="flex items-center gap-3 mb-1">
                    <div className="w-8 h-8 bg-industrial-accent rounded-lg flex items-center justify-center font-black text-white shadow-lg shadow-industrial-accent/20">L</div>
                    <h1 className="text-lg font-black text-white tracking-tighter">
                        LEXDOCSPRO <span className="text-industrial-accent">LITE</span>
                    </h1>
                </div>
                <p className="text-[10px] text-slate-500 font-mono font-bold uppercase tracking-widest pl-11">Industrial v2.3.0</p>
            </div>

            <nav className="flex-1 space-y-1">
                <SidebarItem
                    icon={LayoutDashboard} label="Dashboard"
                    active={current === 'dashboard'}
                    onClick={() => onNavigate('dashboard')}
                />
                <SidebarItem
                    icon={Cpu} label="Watchdog PRO"
                    active={current === 'watchdog'}
                    onClick={() => onNavigate('watchdog')}
                />
                <SidebarItem
                    icon={FileText} label="AI Agent v3"
                    active={current === 'agent'}
                    onClick={() => onNavigate('agent')}
                />
                <SidebarItem
                    icon={ShieldCheck} label="Firma Digital"
                    onClick={() => onNavigate('signature')}
                />
                <SidebarItem
                    icon={AlertCircle} label="Modelo 347"
                    active={current === '347'}
                    badge="3"
                    onClick={() => onNavigate('347')}
                />
            </nav>

            <div className="mt-auto space-y-4">
                <div className="bg-slate-900/50 rounded-2xl p-4 border border-slate-800/50">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-[10px] font-bold text-slate-500 uppercase">Uptime</span>
                        <span className="text-[10px] font-mono text-industrial-success">99.9%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                        <div className="bg-industrial-success w-full h-full rounded-full opacity-50"></div>
                    </div>
                </div>
                <SidebarItem icon={Settings} label="Configuración" />
            </div>
        </div>
    );
};

export default Sidebar;
