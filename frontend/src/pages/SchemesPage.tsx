import React, { useEffect, useState } from 'react';
import { Award, ExternalLink, RefreshCw } from 'lucide-react';
import { schemeService } from '../services/scheme';
import { conversationService } from '../services/conversation';
import { SchemeRecommendationResult, SchemeSummaryResponse } from '../types/scheme';
import { SchemeCard } from '../components/schemes/SchemeCard';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { kn } from '../i18n/kannada';

interface SchemesPageProps {
  onStartChat: () => void;
}

export const SchemesPage: React.FC<SchemesPageProps> = ({ onStartChat }) => {
  const [activeTab, setActiveTab] = useState<'recommendations' | 'catalog'>('recommendations');
  const [recommendations, setRecommendations] = useState<SchemeRecommendationResult[]>([]);
  const [catalog, setCatalog] = useState<SchemeSummaryResponse[]>([]);
  const [isReevaluating, setIsReevaluating] = useState<boolean>(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const loadData = async () => {
    try {
      // 1. Fetch catalog
      const cat = await schemeService.list();
      setCatalog(cat);

      // 2. Fetch active conversation recommendations if available
      const active = await conversationService.getActive();
      if (active) {
        setConversationId(active.conversation_id);
        const hist = await schemeService.getHistory(active.conversation_id);
        if (hist && hist.length > 0) {
          // Guaranteed latest recommendation run ordering (M7.2)
          const sorted = [...hist].sort(
            (a, b) => new Date(b.evaluated_at).getTime() - new Date(a.evaluated_at).getTime()
          );
          const latestRun = sorted[0];
          setRecommendations(latestRun.explanation_trace?.recommendations || latestRun.results || []);
        }
      }
    } catch {
      // Fallback
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleEvaluate = async () => {
    if (!conversationId) {
      onStartChat();
      return;
    }
    setIsReevaluating(true);
    try {
      const res = await schemeService.evaluate(conversationId);
      setRecommendations(res.recommendations);
    } catch {
      // Error
    } finally {
      setIsReevaluating(false);
    }
  };

  return (
    <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Title & Statutory Disclaimer */}
      <div>
        <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#1b4d3e', margin: 0 }}>
          {kn.schemes.title}
        </h2>
        <div
          style={{
            backgroundColor: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            padding: '10px 14px',
            marginTop: '8px',
            fontSize: '12px',
            color: '#475569',
            lineHeight: 1.4,
          }}
        >
          <strong style={{ color: '#0f172a' }}>ಗಮನಿಸಿ: </strong>
          {kn.schemes.disclaimer}
        </div>
      </div>

      {/* Tabs: Recommendations vs Catalog */}
      <div style={{ display: 'flex', borderBottom: '2px solid #e2e8f0' }}>
        <button
          onClick={() => setActiveTab('recommendations')}
          style={{
            padding: '10px 16px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'recommendations' ? '3px solid #1b4d3e' : 'none',
            fontWeight: activeTab === 'recommendations' ? 700 : 500,
            color: activeTab === 'recommendations' ? '#1b4d3e' : '#64748b',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          ಶಿಫಾರಸುಗಳು ({recommendations.length})
        </button>
        <button
          onClick={() => setActiveTab('catalog')}
          style={{
            padding: '10px 16px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'catalog' ? '3px solid #1b4d3e' : 'none',
            fontWeight: activeTab === 'catalog' ? 700 : 500,
            color: activeTab === 'catalog' ? '#1b4d3e' : '#64748b',
            cursor: 'pointer',
            fontSize: '14px',
          }}
        >
          ಎಲ್ಲಾ ಯೋಜನೆಗಳು ({catalog.length})
        </button>
      </div>

      {/* Recommendations View */}
      {activeTab === 'recommendations' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {recommendations.length === 0 ? (
            <div
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '16px',
                padding: '28px 20px',
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '12px',
              }}
            >
              <Award size={40} color="#94a3b8" />
              <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: '#1e293b' }}>
                ಯಾವುದೇ ಸಕ್ರಿಯ ಶಿಫಾರಸುಗಳಿಲ್ಲ
              </h3>
              <p style={{ fontSize: '13px', color: '#64748b', margin: 0, maxWidth: '320px' }}>
                ನಿಮ್ಮ ಬೆಳೆ ಮತ್ತು ಜಮೀನಿನ ವಿವರಗಳನ್ನು ಹಂಚಿಕೊಳ್ಳಲು ಧ್ವನಿ ಸಂಭಾಷಣೆ ಆರಂಭಿಸಿ.
              </p>
              <Button
                onClick={onStartChat}
                variant="primary"
                size="md"
              >
                ಸಂಭಾಷಣೆ ಆರಂಭಿಸಿ
              </Button>
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  onClick={handleEvaluate}
                  isLoading={isReevaluating}
                  variant="outline"
                  size="sm"
                  icon={<RefreshCw size={14} />}
                >
                  ಮರುಪರಿಶೀಲಿಸಿ
                </Button>
              </div>

              {recommendations.map((rec) => (
                <SchemeCard key={rec.scheme_id} recommendation={rec} />
              ))}
            </>
          )}
        </div>
      )}

      {/* Catalog View */}
      {activeTab === 'catalog' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {catalog.map((scheme) => (
            <div
              key={scheme.scheme_id}
              style={{
                backgroundColor: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: '14px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              {scheme.demo_only && (
                <div style={{ alignSelf: 'flex-start' }}>
                  <Badge variant="demo" size="sm">
                    {kn.schemes.demoNotice}
                  </Badge>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h4 style={{ fontSize: '16px', fontWeight: 700, color: '#1b4d3e', margin: 0 }}>
                    {scheme.display_name_kn}
                  </h4>
                  <p style={{ fontSize: '12px', color: '#64748b', margin: '2px 0 0 0' }}>
                    {scheme.display_name}
                  </p>
                </div>
                <Badge variant={scheme.classification === 'REAL_GOVERNMENT' ? 'success' : 'neutral'} size="sm">
                  {scheme.classification === 'REAL_GOVERNMENT' ? 'ಸರ್ಕಾರಿ ಯೋಜನೆ' : 'ಡೆಮೊ ಯೋಜನೆ'}
                </Badge>
              </div>

              <p style={{ fontSize: '13px', color: '#334155', margin: 0 }}>
                {scheme.summary_kn || scheme.summary}
              </p>

              {scheme.application_portal && (
                <a
                  href={scheme.application_portal}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    fontSize: '12px',
                    color: '#1b4d3e',
                    fontWeight: 600,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    textDecoration: 'none',
                    marginTop: '4px',
                  }}
                >
                  <span>ಅಧಿಕೃತ ಪೋರ್ಟಲ್: {scheme.application_portal}</span>
                  <ExternalLink size={12} />
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
