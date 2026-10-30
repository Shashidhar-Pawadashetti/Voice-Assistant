import React from 'react';
import { Mic, X, Send } from 'lucide-react';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { kn } from '../../i18n/kannada';

interface VoiceMicButtonProps {
  onAudioReady: (blob: Blob) => void;
  disabled?: boolean;
}

export const VoiceMicButton: React.FC<VoiceMicButtonProps> = ({ onAudioReady, disabled = false }) => {
  const {
    isRecording,
    recordingDuration,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
  } = useVoiceRecorder(60);

  const handleStopAndSubmit = async () => {
    const blob = await stopRecording();
    if (blob) {
      onAudioReady(blob);
    }
  };

  const formatSeconds = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', width: '100%' }}>
      {error && (
        <div
          role="alert"
          style={{
            backgroundColor: '#ffebee',
            color: '#c62828',
            fontSize: '13px',
            padding: '8px 12px',
            borderRadius: '8px',
            textAlign: 'center',
            maxWidth: '90%',
          }}
        >
          {error}
        </div>
      )}

      {isRecording ? (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '12px',
            width: '100%',
            padding: '16px',
            backgroundColor: '#fff5f5',
            borderRadius: '20px',
            border: '2px solid #ffcdd2',
          }}
        >
          {/* Recording Timer & Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#d90429', fontWeight: 700 }}>
            <span
              style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: '#d90429',
                display: 'inline-block',
                animation: 'pulseWave 1s infinite',
              }}
            />
            <span>{kn.voice.recording}</span>
            <span style={{ fontSize: '18px', fontFamily: 'monospace' }}>
              {formatSeconds(recordingDuration)}
            </span>
          </div>

          <p style={{ fontSize: '12px', color: '#64748b', textAlign: 'center', margin: 0 }}>
            {kn.voice.cannotAutoSubmit}
          </p>

          {/* Action Buttons: Stop & Submit vs Cancel */}
          <div style={{ display: 'flex', gap: '12px', width: '100%', justifyContent: 'center' }}>
            <button
              onClick={cancelRecording}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '12px 20px',
                backgroundColor: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '12px',
                color: '#475569',
                fontWeight: 600,
                fontSize: '15px',
                cursor: 'pointer',
                minHeight: '48px',
              }}
            >
              <X size={18} />
              <span>ರದ್ದುಮಾಡಿ (Cancel)</span>
            </button>

            <button
              onClick={handleStopAndSubmit}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 24px',
                backgroundColor: '#d90429',
                border: 'none',
                borderRadius: '12px',
                color: '#ffffff',
                fontWeight: 700,
                fontSize: '16px',
                cursor: 'pointer',
                minHeight: '48px',
                boxShadow: '0 4px 10px rgba(217, 4, 41, 0.3)',
              }}
            >
              <Send size={18} />
              <span>{kn.voice.stopAndSend}</span>
            </button>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={startRecording}
            disabled={disabled}
            style={{
              width: '84px',
              height: '84px',
              borderRadius: '50%',
              backgroundColor: disabled ? '#cbd5e1' : '#1b4d3e',
              border: '4px solid #95d5b2',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: disabled ? 'not-allowed' : 'pointer',
              boxShadow: disabled ? 'none' : '0 8px 20px rgba(27, 77, 62, 0.35)',
              transition: 'transform 0.15s ease',
            }}
            aria-label={kn.voice.start}
          >
            <Mic size={38} />
          </button>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#1b4d3e' }}>
            {kn.voice.start}
          </span>
        </div>
      )}
    </div>
  );
};
