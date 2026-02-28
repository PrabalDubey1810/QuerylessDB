import { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import WelcomeHero from './components/WelcomeHero';
import ActionCards from './components/ActionCards';
import PromptBar from './components/PromptBar';
import ResultsView from './components/ResultsView';
import SettingsModal from './components/SettingsModal';
import AuditLogView from './components/AuditLogView';
import { sendQuery } from './services/api';
import './App.css';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showHero, setShowHero] = useState(true);

  // Settings & View state
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [userRole, setUserRole] = useState('Viewer');
  const [opMode, setOpMode] = useState('query');
  const [dbType, setDbType] = useState('nosql'); // 'nosql' | 'sql'
  const [currentView, setCurrentView] = useState('chat'); // 'chat' | 'audit'

  const handleQuerySubmit = async (prompt) => {
    setLoading(true);
    setError(null);
    setShowHero(false);

    try {
      const result = await sendQuery(prompt, userRole, opMode, dbType);
      if (result.error) {
        setError(result.error);
      } else {
        setData(result);
      }
    } catch (err) {
      setError(err.message || 'Failed to connect to backend');
    } finally {
      setLoading(false);
    }
  };

  const openSettings = () => setIsSettingsOpen(true);

  return (
    <div className="app-container">
      <Sidebar
        onSettingsClick={openSettings}
        dbType={dbType}
        setDbType={setDbType}
        currentView={currentView}
        setView={setCurrentView}
        role={userRole}
        setRole={setUserRole}
      />
      <Header onSettingsClick={openSettings} dbType={dbType} />

      <main className="main-content">
        <div className="content-wrapper">
          {currentView === 'audit' ? (
            <AuditLogView />
          ) : showHero ? (
            <>
              <WelcomeHero />
              <div className="cards-section">
                <ActionCards />
              </div>
            </>
          ) : (
            <ResultsView data={data} loading={loading} error={error} />
          )}
        </div>

        {currentView === 'chat' && (
          <PromptBar onSubmit={handleQuerySubmit} isLoading={loading} dbType={dbType} />
        )}
      </main>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        role={userRole}
        setRole={setUserRole}
        mode={opMode}
        setMode={setOpMode}
        dbType={dbType}
        setDbType={setDbType}
      />
    </div>
  );
}

export default App;
