import React, { useState } from 'react';
import { Download, CheckCircle2 } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { privacyService } from '../../services/privacy';
import { kn } from '../../i18n/kannada';

interface DataExportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DataExportModal: React.FC<DataExportModalProps> = ({ isOpen, onClose }) => {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [downloadSuccess, setDownloadSuccess] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await privacyService.exportData();
      // Generate JSON download file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `krishi_mitra_data_export_${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setDownloadSuccess(true);
    } catch (err: any) {
      setError(err.message || 'ಡೇಟಾ ಡೌನ್‌ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={kn.privacy.exportTitle}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <p style={{ fontSize: '14px', color: '#475569', margin: 0 }}>
          {kn.privacy.exportDesc}
        </p>

        {downloadSuccess ? (
          <div
            style={{
              backgroundColor: '#f0fdf4',
              border: '1px solid #bbf7d0',
              padding: '14px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              color: '#16a34a',
            }}
          >
            <CheckCircle2 size={24} />
            <div>
              <div style={{ fontWeight: 700 }}>ಡೇಟಾ ಡೌನ್‌ಲೋಡ್ ಯಶಸ್ವಿಯಾಗಿದೆ!</div>
              <div style={{ fontSize: '12px' }}>ನಿಮ್ಮ ಸಾಧನಕ್ಕೆ JSON ಫೈಲ್ ಉಳಿಸಲಾಗಿದೆ.</div>
            </div>
          </div>
        ) : (
          <Button
            onClick={handleExport}
            isLoading={isLoading}
            variant="primary"
            size="lg"
            icon={<Download size={20} />}
            style={{ width: '100%' }}
          >
            {kn.privacy.exportButton}
          </Button>
        )}

        {error && (
          <div style={{ color: '#dc2626', fontSize: '13px', textAlign: 'center' }}>
            {error}
          </div>
        )}
      </div>
    </Modal>
  );
};
