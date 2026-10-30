import React from 'react';
import { Mic, MessageSquare } from 'lucide-react';
import { ConversationTurnDTO } from '../../types/conversation';
import { AudioPlayer } from '../voice/AudioPlayer';

interface TurnBubbleProps {
  turn: ConversationTurnDTO;
}

export const TurnBubble: React.FC<TurnBubbleProps> = ({ turn }) => {
  const isFarmer = turn.role === 'FARMER';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isFarmer ? 'flex-end' : 'flex-start',
        marginBottom: '14px',
        width: '100%',
      }}
    >
      <div
        style={{
          maxWidth: '85%',
          padding: '12px 16px',
          borderRadius: isFarmer ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
          backgroundColor: isFarmer ? '#1b4d3e' : '#f1f5f9',
          color: isFarmer ? '#ffffff' : '#1a202c',
          boxShadow: '0 2px 5px rgba(0,0,0,0.06)',
          fontSize: '15px',
          lineHeight: 1.5,
        }}
      >
        {/* Turn Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '11px',
            fontWeight: 700,
            color: isFarmer ? '#95d5b2' : '#64748b',
            marginBottom: '4px',
          }}
        >
          {isFarmer ? <Mic size={12} /> : <MessageSquare size={12} />}
          <span>{isFarmer ? 'ರೈತರು (Farmer)' : 'ಕೃಷಿ ಮಿತ್ರ (Krishi Mitra)'}</span>
        </div>

        {/* Message Content */}
        <p style={{ margin: 0, wordBreak: 'break-word' }}>
          {isFarmer ? turn.transcript_text : turn.assistant_text}
        </p>

        {/* Assistant Audio Player */}
        {!isFarmer && turn.audio_url && (
          <div style={{ marginTop: '8px' }}>
            <AudioPlayer audioUrl={turn.audio_url} />
          </div>
        )}
      </div>

      <span
        style={{
          fontSize: '10px',
          color: '#94a3b8',
          marginTop: '2px',
          padding: '0 4px',
        }}
      >
        {turn.created_at ? new Date(turn.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
      </span>
    </div>
  );
};
