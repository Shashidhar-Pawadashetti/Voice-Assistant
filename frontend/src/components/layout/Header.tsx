import React from 'react';
import { Sprout, Wifi, WifiOff } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useNetworkStatus } from '../../hooks/useNetworkStatus';
import { kn } from '../../i18n/kannada';

export const Header: React.FC = () => {
  const { farmer } = useAuth();
  const { isOnline } = useNetworkStatus();

  return (
    <header
      style={{
        backgroundColor: '#1b4d3e',
        color: '#ffffff',
        padding: '12px 18px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div
          style={{
            backgroundColor: '#2d6a4f',
            padding: '8px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Sprout size={24} color="#95d5b2" />
        </div>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 700, margin: 0, lineHeight: 1.2 }}>
            {kn.app.title}
          </h1>
          <p style={{ fontSize: '11px', color: '#d8f3dc', margin: 0 }}>
            {kn.app.subtitle}
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Network status beacon */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            fontSize: '12px',
            padding: '4px 8px',
            borderRadius: '8px',
            backgroundColor: isOnline ? 'rgba(56, 176, 0, 0.2)' : 'rgba(217, 4, 41, 0.3)',
            color: isOnline ? '#95d5b2' : '#ffcdd2',
          }}
          title={isOnline ? 'ಆನ್‌ಲೈನ್‌ (Online)' : 'ಆಫ್‌ಲೈನ್‌ (Offline)'}
        >
          {isOnline ? <Wifi size={14} /> : <WifiOff size={14} />}
          <span style={{ display: 'none' }}>{isOnline ? 'Online' : 'Offline'}</span>
        </div>

        {farmer && (
          <div style={{ textAlign: 'right', fontSize: '12px' }}>
            <span style={{ color: '#d8f3dc' }}>ರೈತರು:</span>{' '}
            <strong style={{ color: '#ffffff' }}>{farmer.phone_number_masked}</strong>
          </div>
        )}
      </div>
    </header>
  );
};
