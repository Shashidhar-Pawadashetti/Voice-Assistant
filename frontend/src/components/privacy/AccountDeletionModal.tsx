import React, { useState } from 'react';
import { AlertTriangle, Trash2 } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { privacyService } from '../../services/privacy';
import { useAuth } from '../../context/AuthContext';
import { kn } from '../../i18n/kannada';

interface AccountDeletionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AccountDeletionModal: React.FC<AccountDeletionModalProps> = ({ isOpen, onClose }) => {
  const { logout } = useAuth();
  const [password, setPassword] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) {
      setError('ಖಾತೆಯನ್ನು ಅಳಿಸಲು ಪಾಸ್‌ವರ್ಡ್ ಕಡ್ಡಾಯವಾಗಿದೆ');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await privacyService.deleteAccount({ password, reason });
      await logout();
      onClose();
    } catch (err: any) {
      setError(err.message || 'ಖಾತೆ ಅಳಿಸಲು ವಿಫಲವಾಗಿದೆ. ಪಾಸ್‌ವರ್ಡ್ ಪರಿಶೀಲಿಸಿ.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={kn.privacy.deleteTitle}>
      <form onSubmit={handleDelete} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div
          style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            padding: '12px',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
            color: '#991b1b',
            fontSize: '13px',
          }}
        >
          <AlertTriangle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>{kn.privacy.deleteWarning}</div>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, marginBottom: '6px' }}>
            ಪಾಸ್‌ವರ್ಡ್ ನಮೂದಿಸಿ (Enter Password):
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={kn.privacy.confirmPasswordPlaceholder}
            required
            style={{
              width: '100%',
              padding: '12px 14px',
              borderRadius: '10px',
              border: '1px solid #cbd5e1',
              fontSize: '15px',
            }}
          />
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '13px', color: '#64748b', marginBottom: '4px' }}>
            ಕಾರಣ (ಐಚ್ಛಿಕ / Optional Reason):
          </label>
          <input
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="ಉದಾ: ಇನ್ನು ಮುಂದೆ ಕೃಷಿ ಮಾಡುತ್ತಿಲ್ಲ"
            style={{
              width: '100%',
              padding: '10px 14px',
              borderRadius: '10px',
              border: '1px solid #cbd5e1',
              fontSize: '14px',
            }}
          />
        </div>

        {error && (
          <div style={{ color: '#dc2626', fontSize: '13px', textAlign: 'center' }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', gap: '10px', marginTop: '8px' }}>
          <Button
            type="button"
            variant="outline"
            size="md"
            onClick={onClose}
            style={{ flex: 1 }}
          >
            ರದ್ದು (Cancel)
          </Button>
          <Button
            type="submit"
            variant="danger"
            size="md"
            isLoading={isLoading}
            icon={<Trash2 size={18} />}
            style={{ flex: 1.5 }}
          >
            {kn.privacy.deleteButton}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
