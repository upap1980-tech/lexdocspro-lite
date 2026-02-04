import React, { useState } from 'react'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './components/Dashboard'
import AIAgentPanel from './components/AIAgentPanel'
import WatchdogMonitor from './components/WatchdogMonitor'
import SignatureModal from './components/SignatureModal'
import ToastSystem from './components/ToastSystem'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [isSignatureModalOpen, setSignatureModalOpen] = useState(false);

  // Mapeo simple de componentes para SPA "lite"
  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard': return <Dashboard />;
      case 'agent': return <AIAgentPanel />;
      case 'watchdog': return <WatchdogMonitor />;
      case '347': return <div className="p-8 mt-16 ml-64 bg-industrial-dark min-h-screen text-white">Sección Modelo 347 en desarrollo...</div>;
      default: return <Dashboard />;
    }
  };

  return (
    <div className="bg-industrial-dark min-h-screen font-sans selection:bg-industrial-accent/30 selection:text-industrial-accent">
      <Sidebar
        current={currentPage}
        onNavigate={(page) => {
          if (page === 'signature') setSignatureModalOpen(true);
          else setCurrentPage(page);
        }}
      />

      <div className="flex flex-col flex-1">
        <Header />
        <main>
          {renderPage()}
        </main>
      </div>

      <SignatureModal
        isOpen={isSignatureModalOpen}
        onClose={() => setSignatureModalOpen(false)}
      />

      <ToastSystem />

      {/* Estilos globales dinámicos para animaciones */}
      <style dangerouslySetInnerHTML={{
        __html: `
        @keyframes slide-in {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        .animate-slide-in {
          animation: slide-in 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .animate-spin-slow {
          animation: spin 3s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1E293B; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #3B82F6; }
      `}} />
    </div>
  )
}

export default App
