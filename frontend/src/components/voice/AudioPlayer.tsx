import React from 'react';
import { Volume2, VolumeX, Loader2 } from 'lucide-react';
import { useAudioPlayer } from '../../hooks/useAudioPlayer';
import { kn } from '../../i18n/kannada';

interface AudioPlayerProps {
  audioUrl: string;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ audioUrl }) => {
  const { isPlaying, isLoading, currentAudioPath, play, stop, error } = useAudioPlayer();

  const isCurrentAudioPlaying = isPlaying && currentAudioPath === audioUrl;

  const handleToggle = () => {
    if (isCurrentAudioPlaying) {
      stop();
    } else {
      play(audioUrl);
    }
  };

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
      <button
        onClick={handleToggle}
        disabled={isLoading}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 12px',
          backgroundColor: isCurrentAudioPlaying ? '#2d6a4f' : '#e8f5e9',
          color: isCurrentAudioPlaying ? '#ffffff' : '#1b4d3e',
          border: '1px solid #c8e6c9',
          borderRadius: '20px',
          fontSize: '13px',
          fontWeight: 600,
          cursor: 'pointer',
          minHeight: '36px',
        }}
        aria-label={isCurrentAudioPlaying ? kn.voice.stopAudio : kn.voice.playAudio}
      >
        {isLoading ? (
          <Loader2 className="spinner" size={16} />
        ) : isCurrentAudioPlaying ? (
          <VolumeX size={16} />
        ) : (
          <Volume2 size={16} />
        )}
        <span>{isCurrentAudioPlaying ? kn.voice.stopAudio : kn.voice.playAudio}</span>
      </button>

      {error && (
        <span style={{ fontSize: '11px', color: '#c62828' }}>{error}</span>
      )}
    </div>
  );
};
