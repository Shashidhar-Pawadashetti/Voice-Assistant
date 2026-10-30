import React, { useState } from 'react';
import { ExternalLink, ChevronDown, ChevronUp, AlertTriangle, ShieldCheck } from 'lucide-react';
import { SchemeRecommendationResult } from '../../types/scheme';
import { Badge } from '../common/Badge';
import { kn } from '../../i18n/kannada';

interface SchemeCardProps {
  recommendation: SchemeRecommendationResult;
}

export const SchemeCard: React.FC<SchemeCardProps> = ({ recommendation }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const trace = recommendation.explanation_trace;

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'POTENTIALLY_MATCHED':
        return 'success';
      case 'INSUFFICIENT_INFORMATION':
        return 'warning';
      case 'VERIFICATION_REQUIRED':
        return 'info';
      case 'NOT_MATCHED':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  const getStatusLabel = (status: string) => {
    return (kn.schemes.status as Record<string, string>)[status] || status;
  };

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '18px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Synthetic Demo Warning Ribbon */}
      {recommendation.demo_only && (
        <div
          style={{
            backgroundColor: '#fff3e0',
            borderBottom: '1px solid #ffe082',
            margin: '-18px -18px 8px -18px',
            padding: '6px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            fontWeight: 700,
            color: '#e65100',
          }}
        >
          <AlertTriangle size={14} />
          <span>{kn.schemes.demoNotice}</span>
        </div>
      )}

      {/* Header: Title and Badges */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
        <div>
          <h4 style={{ fontSize: '18px', fontWeight: 700, color: '#1b4d3e', margin: 0 }}>
            {recommendation.display_name_kn}
          </h4>
          <p style={{ fontSize: '12px', color: '#64748b', margin: '2px 0 0 0' }}>
            {recommendation.display_name} ({recommendation.scheme_id})
          </p>
        </div>

        <Badge variant={getStatusBadgeVariant(recommendation.recommendation_status)}>
          {getStatusLabel(recommendation.recommendation_status)}
        </Badge>
      </div>

      {/* Grounded Native Kannada Explanation */}
      <p style={{ fontSize: '14px', color: '#334155', lineHeight: 1.5, margin: 0 }}>
        {trace.kannada_explanation}
      </p>

      {/* Official Verification Disclaimer */}
      {recommendation.official_verification_required && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            color: '#0284c7',
            backgroundColor: '#f0f9ff',
            padding: '8px 12px',
            borderRadius: '10px',
            border: '1px solid #bae6fd',
          }}
        >
          <ShieldCheck size={16} />
          <span>{kn.schemes.officialVerificationRequired}</span>
        </div>
      )}

      {/* Application Portal Link */}
      {recommendation.application_portal && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}>
          <span style={{ fontWeight: 600, color: '#64748b' }}>{kn.schemes.officialPortal}</span>
          <a
            href={recommendation.application_portal}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: '#1b4d3e',
              fontWeight: 700,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              textDecoration: 'none',
            }}
          >
            <span>{recommendation.application_portal}</span>
            <ExternalLink size={14} />
          </a>
        </div>
      )}

      {/* Expand/Collapse Detailed Condition Trace */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          background: 'none',
          border: 'none',
          padding: '6px 0',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          color: '#2d6a4f',
          fontWeight: 600,
          fontSize: '13px',
          borderTop: '1px solid #f1f5f9',
          marginTop: '4px',
        }}
      >
        <span>{kn.schemes.viewDetails}</span>
        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {isExpanded && (
        <div
          style={{
            backgroundColor: '#f8fafc',
            borderRadius: '12px',
            padding: '12px',
            fontSize: '13px',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
          }}
        >
          {trace.matched_conditions?.length > 0 && (
            <div>
              <strong style={{ color: '#16a34a' }}>{kn.schemes.matchedConditions}</strong>
              <ul style={{ paddingLeft: '18px', margin: '4px 0', color: '#334155' }}>
                {trace.matched_conditions.map((c, i) => (
                  <li key={i}>{c.field_name}: {JSON.stringify(c.expected_value)}</li>
                ))}
              </ul>
            </div>
          )}

          {trace.failed_conditions?.length > 0 && (
            <div>
              <strong style={{ color: '#dc2626' }}>{kn.schemes.failedConditions}</strong>
              <ul style={{ paddingLeft: '18px', margin: '4px 0', color: '#334155' }}>
                {trace.failed_conditions.map((c, i) => (
                  <li key={i}>{c.field_name} ({c.reason || 'ಅರ್ಹತೆಯಿಲ್ಲ'})</li>
                ))}
              </ul>
            </div>
          )}

          {trace.unknown_conditions?.length > 0 && (
            <div>
              <strong style={{ color: '#d97706' }}>{kn.schemes.unknownConditions}</strong>
              <ul style={{ paddingLeft: '18px', margin: '4px 0', color: '#334155' }}>
                {trace.unknown_conditions.map((c, i) => (
                  <li key={i}>{c.field_name} (ಪರಿಶೀಲಿಸಬೇಕು)</li>
                ))}
              </ul>
            </div>
          )}

          <div style={{ fontSize: '11px', color: '#94a3b8', borderTop: '1px solid #e2e8f0', paddingTop: '6px' }}>
            <span>{kn.schemes.ruleVersion} {trace.rule_version}</span>
            {trace.evidence_references?.length > 0 && (
              <span> • ಆಧಾರ: {trace.evidence_references[0].authority}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
