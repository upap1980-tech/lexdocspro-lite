import React from 'react';
import { Shield, FileCheck, X, LucideShieldCheck, Lock, Fingerprint, Calendar, Terminal } from 'lucide-react';

const SignatureModal = ({ isOpen, onClose }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-industrial-dark/90 backdrop-blur-md" onClick={onClose}></div>

            <div className="relative bg-industrial-card border border-slate-700/50 w-full max-w-2xl rounded-[32px] overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)]">
                <div className="p-6 border-b border-slate-800 bg-slate-900 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-2xl bg-industrial-accent/20 flex items-center justify-center text-industrial-accent border border-industrial-accent/20">
                            <Shield size={20} />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-white">Sellado Digital PAdES</h3>
                            <p className="text-[10px] text-slate-500 font-mono uppercase">Módulo de Seguridad v3.1.0 PRO</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-full text-slate-500 transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="p-8">
                    <div className="grid grid-cols-2 gap-8 mb-8">
                        <div className="space-y-4">
                            <div className="p-4 bg-industrial-dark border border-slate-800 rounded-2xl">
                                <label className="text-[10px] text-slate-500 uppercase font-mono mb-3 block">Documento a Firmar</label>
                                <div className="flex items-center gap-3">
                                    <FileCheck className="text-industrial-accent" size={24} />
                                    <div>
                                        <p className="text-xs font-bold text-slate-200">recurso_apelacion.pdf</p>
                                        <p className="text-[10px] text-slate-500">2.4 MB • PDF/A Compliance</p>
                                    </div>
                                </div>
                            </div>

                            <div className="p-4 bg-industrial-dark border border-slate-800 rounded-2xl">
                                <label className="text-[10px] text-slate-500 uppercase font-mono mb-3 block">Certificado Seleccionado</label>
                                <div className="flex items-center gap-3">
                                    <Fingerprint className="text-industrial-success" size={24} />
                                    <div className="flex-1">
                                        <select className="w-full bg-transparent text-xs font-bold text-slate-200 outline-none border-none">
                                            <option>FIRMA_ABOGADO_2024.p12</option>
                                            <option>LEXDOCS_DESARROLLO.p12</option>
                                        </select>
                                        <p className="text-[10px] text-slate-500">Expira: 12/2026</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-6 flex flex-col justify-center items-center text-center">
                            <div className="w-16 h-16 rounded-full bg-industrial-accent/10 flex items-center justify-center text-industrial-accent mb-4 border border-industrial-accent/20 animate-pulse">
                                <Lock size={32} />
                            </div>
                            <h4 className="text-sm font-bold text-white mb-2">Protocolo de Seguridad</h4>
                            <p className="text-[11px] text-slate-500 leading-relaxed">
                                Toda operación de firma queda registrada en el Audit Log persistente. El documento se sellará con el estándar industrial PAdES de Adobe.
                            </p>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="relative">
                            <input
                                type="password"
                                placeholder="Introduzca la contraseña del certificado"
                                className="w-full bg-industrial-dark border border-slate-700 rounded-2xl py-4 px-6 text-sm text-slate-200 outline-none focus:border-industrial-accent transition-all pl-12"
                            />
                            <Lock className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-600" size={16} />
                        </div>

                        <button className="w-full py-4 bg-industrial-accent hover:bg-blue-600 text-white rounded-2xl font-bold flex items-center justify-center gap-2 shadow-xl shadow-industrial-accent/20 transition-all group">
                            <LucideShieldCheck size={20} className="group-hover:scale-110 transition-transform" /> Ejecutar Sellado Digital
                        </button>
                        <p className="text-center text-[10px] text-slate-600 italic">
                            Al firmar, usted confirma la integridad legal de este borrador generado por IA.
                        </p>
                    </div>
                </div>

                <div className="p-4 bg-slate-900/80 border-t border-slate-800 flex items-center gap-4 text-[10px] font-mono text-slate-500 px-8">
                    <span className="flex items-center gap-1.5"><Terminal size={12} /> HASH: 0x82...F41</span>
                    <span className="flex items-center gap-1.5"><Calendar size={12} /> TIMESTAMP: 2026-02-04</span>
                    <div className="ml-auto flex items-center gap-2 bg-industrial-success/10 text-industrial-success px-2 py-0.5 rounded border border-industrial-success/20">
                        <CheckCircle size={10} /> LEGALMENTE VINCULANTE
                    </div>
                </div>
            </div>
        </div>
    );
};

const CheckCircle = ({ size }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
);

export default SignatureModal;
