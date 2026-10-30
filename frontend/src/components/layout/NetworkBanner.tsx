import React from 'react';
import { WifiOff } from 'lucide-react';
import { useNetworkStatus } from '../../hooks/useNetworkStatus';
import { kn } from '../../i18n/kannada';

export const NetworkBanner: React.FC = () => {
  const { isOnline } = useNetworkStatus();

  if (isOnline) return null;

  return (
    <div
      role="alert"
      style={{
        backgroundColor: '#d90429',
        color: '#ffffff',
        padding: '10px 16px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        fontSize: '14px',
        fontWeight: 600,
        position: 'sticky',
        top: 0,
        zIndex: 999,
        boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
      }}
    >
      <WifiOff size={18} />
      <div style={{ flex: 1 }}>
        <div>{kn.network.offline}</div>
        <div style={{ fontSize: '12px', fontWeight: 400, opacity: 0.9 }}>
          {kn.network.offlineWarning}
        </div>
      </div>
    </div>
  );
};
