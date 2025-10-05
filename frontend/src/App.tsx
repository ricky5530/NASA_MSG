import { useState } from 'react';
import ChatArea from './components/ChatArea';
import Dashboard from './components/Dashboard';
import Sidebar from './components/Sidebar';
import './styles/globals.css';

function App() {
  const [currentView, setCurrentView] = useState<'chat' | 'dashboard'>('chat');

  return (
    <div className="App h-screen flex">
      {/* 왼쪽 사이드바 */}
      <Sidebar 
        currentView={currentView}
        onViewChange={setCurrentView}
      />

      {/* 메인 컨텐츠 영역 */}
      <div className="flex-1 overflow-hidden">
        {currentView === 'chat' ? (
          <ChatArea serverConnected={true} />
        ) : (
          <Dashboard />
        )}
      </div>
    </div>
  );
}

export default App;