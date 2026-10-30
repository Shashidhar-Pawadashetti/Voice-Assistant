import React from 'react';
import { Home, Mic, Award, Shield } from 'lucide-react';

export type TabKey = 'home' | 'chat' | 'schemes' | 'privacy';

interface NavigationProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
}

export const Navigation: React.FC<NavigationProps> = ({ activeTab, onTabChange }) => {
  const tabs = [
    { key: 'home', label: 'ಮುಖಪುಟ', icon: <Home size={22} /> },
    { key: 'chat', label: 'ಧ್ವನಿ ಸಂಭಾಷಣೆ', icon: <Mic size={24} /> },
    { key: 'schemes', label: 'ಯೋಜನೆಗಳು', icon: <Award size={22} /> },
    { key: 'privacy', label: 'ಗೌಪ್ಯತೆ', icon: <Shield size={22} /> },
  ];

  return (
    <nav
      style={{
        position: 'sticky',
        bottom: 0,
        backgroundColor: '#ffffff',
        borderTop: '1px solid #e2e8f0',
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        padding: '8px 4px',
        zIndex: 100,
        boxShadow: '0 -2px 10px rgba(0,0,0,0.06)',
      }}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.key;
        return (
          <button
            key={tab.key}
            onClick={() => onTabChange(tab.key as TabKey)}
            style={{
              background: 'transparent',
              border: 'none',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
              padding: '6px 12px',
              color: isActive ? '#1b4d3e' : '#64748b',
              fontWeight: isActive ? 700 : 500,
              cursor: 'pointer',
              minWidth: '64px',
              borderRadius: '8px',
              transition: 'color 0.15s ease',
            }}
          >
            <div
              style={{
                backgroundColor: isActive ? '#e8f5e9' : 'transparent',
                padding: '4px 12px',
                borderRadius: '16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {tab.icon}
            </div>
            <span style={{ fontSize: '11px', lineHeight: 1.1 }}>{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
};
