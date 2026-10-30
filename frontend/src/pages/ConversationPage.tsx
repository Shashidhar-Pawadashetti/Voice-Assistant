import React, { useEffect, useRef, useState } from 'react';
import { Send, Plus, Loader2, AlertCircle, RefreshCw, CheckCircle2 } from 'lucide-react';
import { conversationService } from '../services/conversation';
import { schemeService } from '../services/scheme';
import { revokeAudioBlobUrls } from '../services/audio';
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

interface PendingTurnAttempt {
  mode: 'VOICE' | 'TEXT';
  audioBlob?: Blob;
  text?: string;
  clientTurnId: string;
  expectedVersion?: number | null;
}

export const ConversationPage: React.FC<ConversationPageProps> = ({ onViewRecommendations }) => {
  const [conversation, setConversation] = useState<ConversationResponse | null>(null);
  const [turns, setTurns] = useState<ConversationTurnDTO[]>([]);
  const [textInput, setTextInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [conflictNotice, setConflictNotice] = useState<string | null>(null);
  const [pendingAttempt, setPendingAttempt] = useState<PendingTurnAttempt | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Load or create active conversation
  const initConversation = async () => {
    setIsLoading(true);
    setError(null);
    setConflictNotice(null);
    setPendingAttempt(null);
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
    return () => {
      // Memory cleanup: release all ephemeral audio blob URLs on unmount (M7.2)
      revokeAudioBlobUrls();
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [turns]);

  // Handle Voice Turn Submission with stable turn ID and optimistic versioning (M7.2)
  const handleAudioReady = async (audioBlob: Blob, retryTurnId?: string) => {
    if (!conversation) return;
    const clientTurnId = retryTurnId || crypto.randomUUID();
    setIsSubmitting(true);
    setError(null);
    setConflictNotice(null);

    try {
      const turnRes: TurnResponse = await conversationService.submitVoiceTurn(
        conversation.conversation_id,
        audioBlob,
        conversation.version,
        clientTurnId
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
      setPendingAttempt(null);

      // Refresh conversation state and slots
      const refreshed = await conversationService.getById(conversation.conversation_id);
      setConversation(refreshed);
    } catch (err: any) {
      if (err.statusCode === 409 || err.code === 'CONCURRENCY_CONFLICT') {
        // HTTP 409 Conflict Recovery (M7.2)
        setConflictNotice('ಸಂಭಾಷಣೆಯ ಸ್ಥಿತಿ ಸರ್ವರ್‌ನಲ್ಲಿ ಬದಲಾಗಿದೆ, ಸ್ವಯಂ-ನವೀಕರಿಸಲಾಗಿದೆ. ದಯವಿಟ್ಟು ಮುಂದುವರಿಸಿ.');
        const refreshed = await conversationService.getById(conversation.conversation_id);
        setConversation(refreshed);
        setPendingAttempt(null);
      } else {
        setError(err.message || 'ಧ್ವನಿ ಪ್ರಕ್ರಿಯೆ ವಿಫಲವಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.');
        setPendingAttempt({
          mode: 'VOICE',
          audioBlob,
          clientTurnId,
          expectedVersion: conversation.version,
        });
      }
    } finally {
      setIsSubmitting(false);
      setTimeout(scrollToBottom, 150);
    }
  };

  // Execute Text Turn with stable idempotency key across retries
  const executeTextTurn = async (message: string, retryTurnId?: string) => {
    if (!conversation) return;
    const clientTurnId = retryTurnId || crypto.randomUUID();
    setIsSubmitting(true);
    setError(null);
    setConflictNotice(null);

    try {
      const turnRes = await conversationService.submitTextTurn(
        conversation.conversation_id,
        message,
        conversation.version,
        clientTurnId
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
      setPendingAttempt(null);

      const refreshed = await conversationService.getById(conversation.conversation_id);
      setConversation(refreshed);
    } catch (err: any) {
      if (err.statusCode === 409 || err.code === 'CONCURRENCY_CONFLICT') {
        // HTTP 409 Conflict Recovery (M7.2)
        setConflictNotice('ಸಂಭಾಷಣೆಯ ಸ್ಥಿತಿ ಸರ್ವರ್‌ನಲ್ಲಿ ಬದಲಾಗಿದೆ, ಸ್ವಯಂ-ನವೀಕರಿಸಲಾಗಿದೆ. ದಯವಿಟ್ಟು ಮುಂದುವರಿಸಿ.');
        const refreshed = await conversationService.getById(conversation.conversation_id);
        setConversation(refreshed);
        setPendingAttempt(null);
      } else {
        setError(err.message || 'ಸಂದೇಶ ಕಳುಹಿಸಲು ವಿಫಲವಾಗಿದೆ');
        setPendingAttempt({
          mode: 'TEXT',
          text: message,
          clientTurnId,
          expectedVersion: conversation.version,
        });
      }
    } finally {
      setIsSubmitting(false);
      setTimeout(scrollToBottom, 150);
    }
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim() || !conversation || isSubmitting) return;
    const message = textInput.trim();
    setTextInput('');
    await executeTextTurn(message);
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

        {/* Conflict Auto-Recovery Banner (M7.2) */}
        {conflictNotice && (
          <div
            role="status"
            style={{
              backgroundColor: '#ecfdf5',
              color: '#065f46',
              padding: '10px 14px',
              borderRadius: '12px',
              border: '1px solid #a7f3d0',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <CheckCircle2 size={16} />
            <span>{conflictNotice}</span>
          </div>
        )}

        {/* Error Banner with Explicit Retry Controls (M7.2) */}
        {error && (
          <div
            role="alert"
            style={{
              backgroundColor: '#fef2f2',
              color: '#991b1b',
              padding: '12px 14px',
              borderRadius: '12px',
              border: '1px solid #fecaca',
              fontSize: '13px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>

            {pendingAttempt && !isSubmitting && (
              <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                <button
                  type="button"
                  onClick={() => {
                    if (pendingAttempt.mode === 'VOICE' && pendingAttempt.audioBlob) {
                      handleAudioReady(pendingAttempt.audioBlob, pendingAttempt.clientTurnId);
                    } else if (pendingAttempt.mode === 'TEXT' && pendingAttempt.text) {
                      executeTextTurn(pendingAttempt.text, pendingAttempt.clientTurnId);
                    }
                  }}
                  style={{
                    backgroundColor: '#991b1b',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '6px 12px',
                    fontSize: '12px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  <RefreshCw size={14} />
                  <span>ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ (Retry)</span>
                </button>
              </div>
            )}
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
        {/* Central Large Voice Button (Never auto-submits) */}
        <VoiceMicButton onAudioReady={(blob) => handleAudioReady(blob)} disabled={isSubmitting} />

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
