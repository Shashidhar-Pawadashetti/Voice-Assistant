import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Header } from './components/layout/Header';
import { Navigation, TabKey } from './components/layout/Navigation';
import { NetworkBanner } from './components/layout/NetworkBanner';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { ConversationPage } from './pages/ConversationPage';
import { SchemesPage } from './pages/SchemesPage';
import { SettingsPrivacyPage } from './pages/SettingsPrivacyPage';
import { Sprout } from 'lucide-react';
import { kn } from './i18n/kannada';

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [authView, setAuthView] = useState<'login' | 'register'>('login');
  const [currentTab, setCurrentTab] = useState<TabKey>('home');

  if (isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          backgroundColor: '#1b4d3e',
          color: '#ffffff',
          gap: '16px',
        }}
      >
        <div style={{ animation: 'pulseWave 1.5s infinite' }}>
          <Sprout size={48} color="#95d5b2" />
        </div>
        <div style={{ fontSize: '18px', fontWeight: 700 }}>{kn.app.title}</div>
        <div style={{ fontSize: '13px', color: '#d8f3dc' }}>ಲೋಡ್ ಆಗುತ್ತಿದೆ... (Loading...)</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="app-container">
        <NetworkBanner />
        <header
          style={{
            backgroundColor: '#1b4d3e',
            color: '#ffffff',
            padding: '16px',
            textAlign: 'center',
          }}
        >
          <h1 style={{ fontSize: '20px', fontWeight: 700, margin: 0 }}>{kn.app.title}</h1>
          <p style={{ fontSize: '12px', color: '#d8f3dc', margin: '4px 0 0 0' }}>{kn.app.subtitle}</p>
        </header>

        {authView === 'login' ? (
          <LoginPage onSwitchToRegister={() => setAuthView('register')} />
        ) : (
          <RegisterPage onSwitchToLogin={() => setAuthView('login')} />
        )}
      </div>
    );
  }

  return (
    <div className="app-container">
      <NetworkBanner />
      <Header />

      <main style={{ flex: 1, overflowY: 'auto' }}>
        {currentTab === 'home' && (
          <DashboardPage
            onStartChat={() => setCurrentTab('chat')}
            onOpenSchemes={() => setCurrentTab('schemes')}
          />
        )}
        {currentTab === 'chat' && (
          <ConversationPage
            onViewRecommendations={() => setCurrentTab('schemes')}
          />
        )}
        {currentTab === 'schemes' && (
          <SchemesPage
            onStartChat={() => setCurrentTab('chat')}
          />
        )}
        {currentTab === 'privacy' && <SettingsPrivacyPage />}
      </main>

      <Navigation activeTab={currentTab} onTabChange={setCurrentTab} />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
