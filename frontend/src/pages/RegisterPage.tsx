import React, { useState } from 'react';
import { Sprout, UserPlus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { kn } from '../i18n/kannada';

interface RegisterPageProps {
  onSwitchToLogin: () => void;
}

export const RegisterPage: React.FC<RegisterPageProps> = ({ onSwitchToLogin }) => {
  const { register } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [consentGiven, setConsentGiven] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (phoneNumber.length < 10) {
      setError('ದಯವಿಟ್ಟು ಮಾನ್ಯವಾದ 10 ಅಂಕಿಗಳ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ');
      return;
    }
    if (password.length < 8) {
      setError('ಪಾಸ್‌ವರ್ಡ್ ಕನಿಷ್ಠ 8 ಅಕ್ಷರಗಳನ್ನು ಹೊಂದಿರಬೇಕು');
      return;
    }
    if (!consentGiven) {
      setError('ಖಾತೆ ತೆರೆಯಲು ದಯವಿಟ್ಟು ನಿಯಮಾವಳಿಗಳಿಗೆ ಒಪ್ಪಿಗೆ ನೀಡಿ');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await register({
        phone_number: phoneNumber,
        password,
        preferred_language: 'kn',
        consent_given: consentGiven,
      });
    } catch (err: any) {
      setError(err.message || 'ನೋಂದಣಿ ವಿಫಲವಾಗಿದೆ. ದಯವಿಟ್ಟು ವಿವರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '32px 20px',
        flex: 1,
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '400px',
          backgroundColor: '#ffffff',
          borderRadius: '20px',
          padding: '28px',
          boxShadow: '0 4px 15px rgba(0,0,0,0.06)',
          border: '1px solid #e2e8f0',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div
            style={{
              width: '56px',
              height: '56px',
              backgroundColor: '#1b4d3e',
              borderRadius: '16px',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '12px',
            }}
          >
            <Sprout size={32} color="#95d5b2" />
          </div>
          <h2 style={{ fontSize: '22px', fontWeight: 700, color: '#1b4d3e', margin: 0 }}>
            {kn.auth.registerTitle}
          </h2>
          <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
            {kn.app.subtitle}
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
              ಮೊಬೈಲ್ ಸಂಖ್ಯೆ (Mobile Number)
            </label>
            <input
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value.replace(/[^0-9]/g, ''))}
              placeholder="10 ಅಂಕಿಗಳ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ"
              maxLength={10}
              required
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '12px',
                border: '1px solid #cbd5e1',
                fontSize: '16px',
                fontFamily: 'monospace',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '14px', fontWeight: 600, color: '#334155', marginBottom: '6px' }}>
              ಪಾಸ್‌ವರ್ಡ್ (Password - min 8 chars)
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="ಪಾಸ್‌ವರ್ಡ್"
              minLength={8}
              required
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '12px',
                border: '1px solid #cbd5e1',
                fontSize: '16px',
              }}
            />
          </div>

          {/* Consent Checkbox */}
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginTop: '4px' }}>
            <input
              type="checkbox"
              id="consent"
              checked={consentGiven}
              onChange={(e) => setConsentGiven(e.target.checked)}
              style={{ width: '18px', height: '18px', marginTop: '2px', accentColor: '#1b4d3e' }}
            />
            <label htmlFor="consent" style={{ fontSize: '12px', color: '#475569', lineHeight: 1.4 }}>
              {kn.auth.consentNotice}
            </label>
          </div>

          {error && (
            <div
              role="alert"
              style={{
                backgroundColor: '#ffebee',
                color: '#c62828',
                fontSize: '13px',
                padding: '10px 12px',
                borderRadius: '10px',
                textAlign: 'center',
              }}
            >
              {error}
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={isLoading}
            icon={<UserPlus size={20} />}
            style={{ width: '100%', marginTop: '8px' }}
          >
            {kn.auth.registerButton}
          </Button>

          <div style={{ textAlign: 'center', marginTop: '12px' }}>
            <button
              type="button"
              onClick={onSwitchToLogin}
              style={{
                background: 'none',
                border: 'none',
                color: '#1b4d3e',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
                textDecoration: 'underline',
              }}
            >
              {kn.auth.alreadyHaveAccount}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
