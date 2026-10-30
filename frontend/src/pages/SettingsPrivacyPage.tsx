import React, { useState } from 'react';
import { User, Shield, Download, Trash2, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { DataExportModal } from '../components/privacy/DataExportModal';
import { AccountDeletionModal } from '../components/privacy/AccountDeletionModal';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { kn } from '../i18n/kannada';

export const SettingsPrivacyPage: React.FC = () => {
  const { farmer, logout } = useAuth();
  const [isExportModalOpen, setIsExportModalOpen] = useState<boolean>(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false);

  return (
    <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Account Profile Card */}
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '16px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              backgroundColor: '#e8f5e9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#1b4d3e',
            }}
          >
            <User size={24} />
          </div>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 700, margin: 0, color: '#1e293b' }}>
              {farmer?.phone_number_masked || 'ರೈತರು'}
            </h3>
            <p style={{ fontSize: '12px', color: '#64748b', margin: '2px 0 0 0' }}>
              ಖಾತೆ ಸಕ್ರಿಯವಾಗಿದೆ (Account Active)
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
          <Badge variant="success" size="sm">
            ಭಾಷೆ: {farmer?.preferred_language === 'kn' ? 'ಕನ್ನಡ (kn)' : farmer?.preferred_language}
          </Badge>
          <Badge variant="neutral" size="sm">
            ಸ್ಥಿತಿ: {farmer?.account_status}
          </Badge>
        </div>
      </div>

      {/* DPDP Act 2023 Rights Section */}
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '16px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Shield size={22} color="#1b4d3e" />
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: '#1b4d3e' }}>
              {kn.privacy.title}
            </h3>
            <p style={{ fontSize: '12px', color: '#64748b', margin: '2px 0 0 0' }}>
              {kn.privacy.subtitle}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '1px solid #f1f5f9', paddingTop: '14px' }}>
          {/* Data Portability / Export */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: '14px' }}>{kn.privacy.exportTitle}</div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>ಎಲ್ಲಾ ಸಂಭಾಷಣೆಗಳು ಮತ್ತು ವಿವರಗಳನ್ನು JSON ರೂಪದಲ್ಲಿ ಪಡೆಯಿರಿ.</div>
            </div>
            <Button
              onClick={() => setIsExportModalOpen(true)}
              variant="outline"
              size="sm"
              icon={<Download size={16} />}
            >
              ಡೌನ್‌ಲೋಡ್
            </Button>
          </div>

          {/* Account & Data Erasure */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px', borderTop: '1px solid #f1f5f9', paddingTop: '12px' }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: '14px', color: '#d90429' }}>{kn.privacy.deleteTitle}</div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>ವೈಯಕ್ತಿಕ ವಿವರಗಳು ಮತ್ತು ಸಂಭಾಷಣೆಗಳನ್ನು ಶಾಶ್ವತವಾಗಿ ಅಳಿಸಿಹಾಕಿ.</div>
            </div>
            <Button
              onClick={() => setIsDeleteModalOpen(true)}
              variant="danger"
              size="sm"
              icon={<Trash2 size={16} />}
            >
              ಅಳಿಸಿ
            </Button>
          </div>
        </div>
      </div>

      {/* Logout Button */}
      <div style={{ marginTop: '10px' }}>
        <Button
          onClick={logout}
          variant="outline"
          size="lg"
          icon={<LogOut size={20} />}
          style={{ width: '100%', borderColor: '#cbd5e1', color: '#475569' }}
        >
          {kn.nav.logout}
        </Button>
      </div>

      {/* Modals */}
      <DataExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
      />

      <AccountDeletionModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
      />
    </div>
  );
};
