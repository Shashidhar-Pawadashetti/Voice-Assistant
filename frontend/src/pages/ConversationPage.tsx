import React, { useEffect, useRef, useState } from 'react';
import { Send, Plus, Loader2, AlertCircle } from 'lucide-react';
import { conversationService } from '../services/conversation';
import { schemeService } from '../services/scheme';
import {
  ConversationResponse,
  ConversationTurnDTO,
  TurnResponse,
} from '../types/conversation';
import { TurnBubble } from '../components/conversation/TurnBubble';
import { SlotFactList } from '../components/conversation/SlotFactList';
import { VoiceMicButton } from '../components/voice/VoiceMicButton';
import { Badge } from '../components/common/Badge';
import { kn } from '../i18n/kannada';

interface ConversationPageProps {
  onViewRecommendations: () => void;
}

export const ConversationPage: React.FC<ConversationPageProps> = ({ onViewRecommendations }) => {
  const [conversation, setConversation] = useState<ConversationResponse | null>(null);
  const [turns, setTurns] = useState<ConversationTurnDTO[]>([]);
  const [textInput, setTextInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Load or create active conversation
  const initConversation = async () => {
    setIsLoading(true);
    setError(null);
    try {
      let active = await conversationService.getActive();
      if (!active) {
        active = await conversationService.create('kn');
      }
      setConversation(active);
      const loadedTurns = await conversationService.getTurns(active.conversation_id);
      setTurns(loadedTurns);
    } catch (err: any) {
      setError(err.message || 'ಸಂಭಾಷಣೆ ಲೋಡ್ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ');
    } finally {
      setIsLoading(false);
      setTimeout(scrollToBottom, 150);
    }
  };

  useEffect(() => {
    initConversation();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [turns]);

  // Handle Voice Turn Submission
  const handleAudioReady = async (audioBlob: Blob) => {
    if (!conversation) return;
    setIsSubmitting(true);
    setError(null);

    try {
      const turnRes: TurnResponse = await conversationService.submitVoiceTurn(
        conversation.conversation_id,
        audioBlob
      );

      // Append turns locally
      const farmerTurn: ConversationTurnDTO = {
        turn_number: turnRes.turn_number,
        role: 'FARMER',
        input_mode: 'VOICE',
        transcript_text: turnRes.transcript_text,
        created_at: new Date().toISOString(),
      };

      const assistantTurn: ConversationTurnDTO = {
        turn_number: turnRes.turn_number + 1,
        role: 'ASSISTANT',
        input_mode: 'VOICE',
        assistant_text: turnRes.assistant_text,
        audio_url: turnRes.audio_url,
        created_at: new Date().toISOString(),
      };

      setTurns((prev) => [...prev, farmerTurn, assistantTurn]);

      // Refresh conversation state and slots
      const refreshed = await conversationService.getById(conversation.conversation_id);
      setConversation(refreshed);
    } catch (err: any) {
      setError(err.message || 'ಧ್ವನಿ ಪ್ರಕ್ರಿಯೆ ವಿಫಲವಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.');
    } finally {
      setIsSubmitting(false);
      setTimeout(scrollToBottom, 150);
    }
  };

  // Handle Text Turn Submission (fallback)
  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim() || !conversation || isSubmitting) return;

    const message = textInput.trim();
    setTextInput('');
    setIsSubmitting(true);
    setError(null);

    try {
      const turnRes = await conversationService.submitTextTurn(
        conversation.conversation_id,
        message,
        conversation.version
      );

      const farmerTurn: ConversationTurnDTO = {
        turn_number: turnRes.turn_number,
        role: 'FARMER',
        input_mode: 'TEXT',
        transcript_text: turnRes.transcript_text,
        created_at: new Date().toISOString(),
      };

      const assistantTurn: ConversationTurnDTO = {
        turn_number: turnRes.turn_number + 1,
        role: 'ASSISTANT',
        input_mode: 'TEXT',
        assistant_text: turnRes.assistant_text,
        audio_url: turnRes.audio_url,
        created_at: new Date().toISOString(),
      };

      setTurns((prev) => [...prev, farmerTurn, assistantTurn]);

      const refreshed = await conversationService.getById(conversation.conversation_id);
      setConversation(refreshed);
    } catch (err: any) {
      setError(err.message || 'ಸಂದೇಶ ಕಳುಹಿಸಲು ವಿಫಲವಾಗಿದೆ');
    } finally {
      setIsSubmitting(false);
      setTimeout(scrollToBottom, 150);
    }
  };

  // Trigger Scheme Recommendations
  const handleEvaluate = async () => {
    if (!conversation) return;
    setIsEvaluating(true);
    setError(null);

    try {
      await schemeService.evaluate(conversation.conversation_id);
      onViewRecommendations();
    } catch (err: any) {
      setError(err.message || 'ಯೋಜನೆಗಳ ಮೌಲ್ಯಮಾಪನ ವಿಫಲವಾಗಿದೆ');
    } finally {
      setIsEvaluating(false);
    }
  };

  // Start fresh conversation
  const handleStartNew = async () => {
    if (conversation) {
      try {
        await conversationService.complete(conversation.conversation_id);
      } catch {}
    }
    initConversation();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
      {/* Dialogue Header with State Badge */}
      <div
        style={{
          padding: '12px 16px',
          backgroundColor: '#ffffff',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', color: '#64748b' }}>ಸ್ಥಿತಿ:</span>
          {conversation && (
            <Badge variant="info" size="sm">
              {(kn.dialogue.states as Record<string, string>)[conversation.state] || conversation.state}
            </Badge>
          )}
        </div>

        <button
          onClick={handleStartNew}
          style={{
            background: 'none',
            border: 'none',
            color: '#1b4d3e',
            fontSize: '12px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <Plus size={16} />
          <span>ಹೊಸ ಸಂಭಾಷಣೆ</span>
        </button>
      </div>

      {/* Main Conversation Scrollable Area */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        {isLoading && (
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '24px', color: '#64748b', gap: '8px' }}>
            <Loader2 className="spinner" size={20} />
            <span>ಸಂಭಾಷಣೆ ಲೋಡ್ ಆಗುತ್ತಿದೆ...</span>
          </div>
        )}

        {/* Slot Fact Summary Card */}
        {conversation && (
          <div style={{ marginBottom: '12px' }}>
            <SlotFactList
              slots={conversation.slots}
              missingSlots={conversation.missing_slots}
              isEvaluationReady={conversation.state === 'EVALUATION_READY'}
              onEvaluate={handleEvaluate}
              isEvaluating={isEvaluating}
            />
          </div>
        )}

        {/* Turn Messages */}
        {turns.map((turn, idx) => (
          <TurnBubble key={idx} turn={turn} />
        ))}

        {isSubmitting && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 14px',
              backgroundColor: '#f1f5f9',
              borderRadius: '12px',
              alignSelf: 'flex-start',
              fontSize: '13px',
              color: '#475569',
            }}
          >
            <Loader2 className="spinner" size={16} />
            <span>ಕೃಷಿ ಮಿತ್ರ ಆಲಿಸುತ್ತಿದೆ ಮತ್ತು ವಿಶ್ಲೇಷಿಸುತ್ತಿದೆ...</span>
          </div>
        )}

        {error && (
          <div
            role="alert"
            style={{
              backgroundColor: '#fef2f2',
              color: '#991b1b',
              padding: '10px 14px',
              borderRadius: '12px',
              border: '1px solid #fecaca',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Voice & Text Interaction Dock */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderTop: '1px solid #e2e8f0',
          padding: '12px 16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          boxShadow: '0 -2px 10px rgba(0,0,0,0.04)',
        }}
      >
        {/* Central Large Voice Button */}
        <VoiceMicButton onAudioReady={handleAudioReady} disabled={isSubmitting} />

        {/* Text Fallback Input */}
        <form onSubmit={handleTextSubmit} style={{ display: 'flex', gap: '8px', width: '100%' }}>
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder={kn.voice.textFallbackPlaceholder}
            disabled={isSubmitting}
            style={{
              flex: 1,
              padding: '10px 14px',
              borderRadius: '12px',
              border: '1px solid #cbd5e1',
              fontSize: '14px',
            }}
          />
          <button
            type="submit"
            disabled={isSubmitting || !textInput.trim()}
            style={{
              padding: '10px 16px',
              backgroundColor: textInput.trim() ? '#1b4d3e' : '#e2e8f0',
              color: textInput.trim() ? '#ffffff' : '#94a3b8',
              border: 'none',
              borderRadius: '12px',
              cursor: textInput.trim() ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            aria-label={kn.voice.sendText}
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};
