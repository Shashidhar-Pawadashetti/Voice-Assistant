import React, { useEffect, useState } from 'react';
import { Mic, ArrowRight, BookOpen, Clock, ShieldCheck } from 'lucide-react';
import { conversationService } from '../services/conversation';
import { ConversationResponse } from '../types/conversation';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { kn } from '../i18n/kannada';

interface DashboardPageProps {
  onStartChat: () => void;
  onOpenSchemes: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onStartChat, onOpenSchemes }) => {
  const [activeConv, setActiveConv] = useState<ConversationResponse | null>(null);

  useEffect(() => {
    conversationService.getActive()
      .then((c) => setActiveConv(c))
      .catch(() => setActiveConv(null));
  }, []);

  return (
    <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Welcome Hero Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #1b4d3e 0%, #2d6a4f 100%)',
          color: '#ffffff',
          borderRadius: '20px',
          padding: '24px 20px',
          boxShadow: '0 4px 12px rgba(27, 77, 62, 0.2)',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        <span style={{ fontSize: '13px', color: '#95d5b2', fontWeight: 600 }}>
          ನಮಸ್ಕಾರ, ರೈತ ಮಿತ್ರರೇ
        </span>
        <h2 style={{ fontSize: '24px', fontWeight: 700, margin: 0, lineHeight: 1.3 }}>
          ಕೃಷಿ ಯೋಜನೆಗಳ ಧ್ವನಿ ಸಹಾಯಕಕ್ಕೆ ಸುಸ್ವಾಗತ
        </h2>
        <p style={{ fontSize: '14px', color: '#d8f3dc', margin: 0, lineHeight: 1.5 }}>
          ನಿಮ್ಮ ಬೆಳೆ, ಜಮೀನು ಮತ್ತು ನೀರಾವರಿ ವಿವರಗಳನ್ನು ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ ಹಂಚಿಕೊಳ್ಳಿ. ನಿಮಗೆ ಅನ್ವಯಿಸುವ ನೈಜ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳನ್ನು ಕಂಡುಕೊಳ್ಳಿ.
        </p>

        <div style={{ marginTop: '8px' }}>
          <Button
            onClick={onStartChat}
            variant="accent"
            size="lg"
            icon={<Mic size={22} />}
            style={{ width: '100%', fontWeight: 700 }}
          >
            {activeConv ? kn.dialogue.resumeConversation : 'ಧ್ವನಿ ಸಂಭಾಷಣೆ ಆರಂಭಿಸಿ (Start Speaking)'}
          </Button>
        </div>
      </div>

      {/* Active Conversation Card */}
      {activeConv && (
        <div
          style={{
            backgroundColor: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: '#64748b' }}>
              <Clock size={16} />
              <span>ಸಕ್ರಿಯ ಸಂಭಾಷಣೆ</span>
            </div>
            <Badge variant="info" size="sm">
              {(kn.dialogue.states as Record<string, string>)[activeConv.state] || activeConv.state}
            </Badge>
          </div>

          <div style={{ fontSize: '14px', fontWeight: 600, color: '#1e293b' }}>
            {activeConv.summary || 'ಕೃಷಿ ಮಾಹಿತಿ ಸಂಗ್ರಹಣೆ ಪ್ರಗತಿಯಲ್ಲಿದೆ...'}
          </div>

          <Button
            onClick={onStartChat}
            variant="outline"
            size="sm"
            icon={<ArrowRight size={16} />}
            style={{ alignSelf: 'flex-start' }}
          >
            ಮುಂದುವರಿಸಿ
          </Button>
        </div>
      )}

      {/* Quick Discovery Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
        <div
          onClick={onOpenSchemes}
          style={{
            backgroundColor: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            padding: '16px',
            cursor: 'pointer',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.03)',
          }}
        >
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              backgroundColor: '#e8f5e9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#1b4d3e',
            }}
          >
            <BookOpen size={20} />
          </div>
          <div style={{ fontSize: '15px', fontWeight: 700, color: '#1b4d3e' }}>
            ಯೋಜನೆಗಳ ಪಟ್ಟಿ
          </div>
          <p style={{ fontSize: '12px', color: '#64748b', margin: 0 }}>
            ಪಿಎಂ-ಕಿಸಾನ್, ಬೆಳೆ ವಿಮೆ ಮತ್ತು ಇತರೆ ಯೋಜನೆಗಳ ಮಾಹಿತಿ.
          </p>
        </div>

        <div
          style={{
            backgroundColor: '#ffffff',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.03)',
          }}
        >
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              backgroundColor: '#fef3c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#d97706',
            }}
          >
            <ShieldCheck size={20} />
          </div>
          <div style={{ fontSize: '15px', fontWeight: 700, color: '#92400e' }}>
            ನೈಜ ನಿಯಮಾವಳಿ
          </div>
          <p style={{ fontSize: '12px', color: '#64748b', margin: 0 }}>
            ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ ಅಲ್ಲ, ಸರ್ಕಾರಿ ನಿಯಮಾವಳಿಗಳ ನೇರ ಲೆಕ್ಕಾಚಾರ.
          </p>
        </div>
      </div>
    </div>
  );
};
