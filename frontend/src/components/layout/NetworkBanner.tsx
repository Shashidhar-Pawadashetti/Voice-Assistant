import React, { useEffect, useState, useRef } from 'react';
import { Wifi, WifiOff } from 'lucide-react';
import { useNetworkStatus } from '../../hooks/useNetworkStatus';
import { kn } from '../../i18n/kannada';

export const NetworkBanner: React.FC = () => {
  const { isOnline } = useNetworkStatus();
  const [showRestoredNotice, setShowRestoredNotice] = useState<boolean>(false);
  const prevOnlineRef = useRef<boolean>(isOnline);

  useEffect(() => {
    // If was offline and now came back online, show recovery notice (M7.2)
    if (!prevOnlineRef.current && isOnline) {
      setShowRestoredNotice(true);
      const timer = setTimeout(() => {
        setShowRestoredNotice(false);
      }, 4000);
      return () => clearTimeout(timer);
    }
    prevOnlineRef.current = isOnline;
  }, [isOnline]);

  if (!isOnline) {
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
  }

  if (showRestoredNotice) {
    return (
      <div
        role="status"
        style={{
          backgroundColor: '#1b4d3e',
          color: '#ffffff',
          padding: '8px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '13px',
          fontWeight: 600,
          position: 'sticky',
          top: 0,
          zIndex: 999,
          boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
          animation: 'fadeIn 0.3s ease-in-out',
        }}
      >
        <Wifi size={16} />
        <span>ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕ ಮರುಸ್ಥಾಪನೆಗೊಂಡಿದೆ (Internet connection restored)</span>
      </div>
    );
  }

  return null;
};
