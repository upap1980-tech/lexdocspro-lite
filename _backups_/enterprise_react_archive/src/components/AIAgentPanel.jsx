import React, { useState } from 'react';
import { Search, Brain, Send, History, Paperclip, Minimize2, ThumbsUp, ThumbsDown, MessageSquare } from 'lucide-react';

const AIContextItem = ({ label, value }) => (
    <div className="flex justify-between items-center py-2 border-b border-slate-800/50">
        <span className="text-[10px] uppercase font-mono text-slate-500">{label}</span>
        <span className="text-xs text-slate-200 font-medium">{value}</span>
    </div>
);

const AIAgentPanel = () => {
    const [messages, setMessages] = useState([
        {
            id: 1,
            role: 'ai',
            content: 'Hola. He analizado el expediente **#DOC-456 (López vs. Banco Central)**. Basado en las notas de estrategia de ayer, sugiero redactar una **Contestación a la Demanda** centrada en la falta de transparencia en los intereses.',
            showFeedback: true
        }
    ]);
    const [learnedDirectives, setLearnedDirectives] = useState([
        "Utilizar tono formal y técnico",
        "Priorizar jurisprudencia del TS 2023"
    ]);

    const handleFeedback = async (msgId, score, comment = "") => {
        try {
            // Enviar a la API real
            const response = await fetch('/api/agent/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    expediente_id: "#DOC-456", // ID dinámico en prod
                    contenido: comment || (score > 0 ? "Me gusta este estilo" : "Corregir estilo"),
                    score: score
                })
            });

            if (response.ok) {
                // Actualizar UI
                setMessages(prev => prev.map(m => m.id === msgId ? { ...m, feedbackDone: true } : m));
            }
        } catch (error) {
            console.error("Error al enviar feedback:", error);
        }
    };
    return (
        <div className="p-8 mt-16 ml-64 bg-industrial-dark min-h-screen flex gap-6">
            <div className="flex-1 flex flex-col bg-industrial-card border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
                <div className="p-4 bg-slate-900 border-b border-slate-800 flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-industrial-accent/20 flex items-center justify-center text-industrial-accent">
                            <Brain size={18} />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-white">AI Agent v3.0</h3>
                            <p className="text-[10px] text-industrial-success font-mono uppercase tracking-widest">En línea / Contexto Activo</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button className="p-2 hover:bg-slate-800 rounded-lg text-slate-500 transition-colors">
                            <Minimize2 size={16} />
                        </button>
                    </div>
                </div>

                <div className="flex-1 p-6 space-y-6 overflow-y-auto custom-scrollbar">
                    {messages.map(msg => (
                        <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                            <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-white font-bold text-xs ${msg.role === 'ai' ? 'bg-industrial-accent' : 'bg-slate-700'}`}>
                                {msg.role === 'ai' ? 'AI' : 'YO'}
                            </div>
                            <div className={`rounded-2xl p-4 max-w-[80%] border ${msg.role === 'ai' ? 'bg-slate-800/50 border-slate-700/30' : 'bg-industrial-accent/10 border-industrial-accent/20'}`}>
                                <p className="text-sm text-slate-200 leading-relaxed" dangerouslySetInnerHTML={{ __html: msg.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }}></p>

                                {msg.role === 'ai' && msg.showFeedback && !msg.feedbackDone && (
                                    <div className="mt-4 pt-3 border-t border-slate-700/50 flex items-center gap-4">
                                        <span className="text-[10px] text-slate-500 font-bold uppercase">¿Es útil esta respuesta?</span>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => handleFeedback(msg.id, 1)}
                                                className="p-1.5 hover:bg-industrial-success/20 rounded text-slate-500 hover:text-industrial-success transition-all"
                                            >
                                                <ThumbsUp size={14} />
                                            </button>
                                            <button
                                                onClick={() => {
                                                    const comment = prompt("¿Cómo podría mejorar?");
                                                    if (comment) handleFeedback(msg.id, -1, comment);
                                                }}
                                                className="p-1.5 hover:bg-industrial-danger/20 rounded text-slate-500 hover:text-industrial-danger transition-all"
                                            >
                                                <ThumbsDown size={14} />
                                            </button>
                                        </div>
                                    </div>
                                )}
                                {msg.feedbackDone && (
                                    <div className="mt-3 text-[10px] text-industrial-success font-bold flex items-center gap-1 animate-pulse">
                                        <Brain size={12} /> Feedback procesado. Aprendiendo estilo...
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                <div className="p-6 bg-industrial-dark/50 border-t border-slate-800">
                    <div className="flex items-center gap-3 bg-industrial-card border border-slate-700 rounded-2xl p-2 pl-4 shadow-xl">
                        <Search className="text-slate-500" size={18} />
                        <input
                            type="text"
                            placeholder="Instrucciones adicionales para el agente..."
                            className="flex-1 bg-transparent border-none outline-none text-sm text-slate-200"
                        />
                        <div className="flex gap-1">
                            <button className="p-2 text-slate-500 hover:text-white transition-colors"><Paperclip size={18} /></button>
                            <button className="bg-industrial-accent p-2 rounded-xl text-white hover:bg-blue-600 shadow-lg shadow-industrial-accent/20 transition-all">
                                <Send size={18} />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <div className="w-80 space-y-6">
                <div className="bg-industrial-card border border-slate-800 p-6 rounded-3xl">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                        <History size={14} /> Contexto del Caso
                    </h4>
                    <div className="space-y-1">
                        <AIContextItem label="Expediente" value="#DOC-456" />
                        <AIContextItem label="Cliente" value="López García, M." />
                        <AIContextItem label="Juzgado" value="1ª Instancia nº 2" />
                        <AIContextItem label="Procedimiento" value="Ordinario" />
                    </div>
                    <div className="mt-6">
                        <label className="text-[10px] text-slate-500 uppercase font-mono mb-2 block">Tonalidad del Agente</label>
                        <div className="grid grid-cols-3 gap-2">
                            <button className="text-[9px] font-bold py-1.5 rounded-lg border border-slate-700 text-slate-400 hover:border-industrial-accent hover:text-white transition-all">Agresivo</button>
                            <button className="text-[9px] font-bold py-1.5 rounded-lg bg-industrial-accent text-white border border-industrial-accent">Neutral</button>
                            <button className="text-[9px] font-bold py-1.5 rounded-lg border border-slate-700 text-slate-400 hover:border-industrial-accent hover:text-white transition-all">Formal</button>
                        </div>
                    </div>
                </div>

                <div className="bg-gradient-to-br from-indigo-900/40 to-slate-900 border border-indigo-500/30 p-6 rounded-3xl">
                    <h4 className="text-[10px] text-indigo-400 font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
                        <Brain size={14} /> Directivas EVO
                    </h4>
                    <div className="space-y-3">
                        {learnedDirectives.map((d, i) => (
                            <div key={i} className="flex gap-3 items-start">
                                <div className="w-1 h-1 rounded-full bg-indigo-500 mt-1.5 shadow-[0_0_5px_rgba(99,102,241,0.5)]"></div>
                                <p className="text-[11px] text-slate-300 leading-relaxed">{d}</p>
                            </div>
                        ))}
                    </div>
                    <div className="mt-4 pt-4 border-t border-indigo-500/20">
                        <p className="text-[9px] text-slate-500 italic">El agente se adapta a tu estilo tras cada interacción.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AIAgentPanel;
