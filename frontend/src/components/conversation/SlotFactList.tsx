import React from 'react';
import { CheckCircle2, HelpCircle, Sparkles } from 'lucide-react';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { kn } from '../../i18n/kannada';

interface SlotFactListProps {
  slots?: Array<{
    slot_key: string;
    canonical_value: any;
    canonical_unit?: string | null;
    status: string;
    provenance: string;
  }>;
  missingSlots: string[];
  isEvaluationReady: boolean;
  onEvaluate: () => void;
  isEvaluating?: boolean;
}

export const SlotFactList: React.FC<SlotFactListProps> = ({
  slots = [],
  missingSlots = [],
  isEvaluationReady,
  onEvaluate,
  isEvaluating = false,
}) => {
  const formatSlotKey = (key: string) => {
    return (kn.profile.fields as Record<string, string>)[key] || key;
  };

  const formatSlotValue = (val: any, unit?: string | null) => {
    if (typeof val === 'object' && val !== null) {
      return JSON.stringify(val);
    }
    return `${val}${unit ? ` ${unit}` : ''}`;
  };

  return (
    <div
      style={{
        backgroundColor: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '16px',
        boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#1b4d3e' }}>
          {kn.profile.title}
        </h3>
        <Badge variant={slots.length > 0 ? 'success' : 'neutral'} size="sm">
          {slots.length} ವಿವರಗಳು
        </Badge>
      </div>

      {slots.length === 0 ? (
        <p style={{ fontSize: '13px', color: '#64748b', margin: 0 }}>
          {kn.profile.empty}
        </p>
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {slots.map((slot) => {
            const isConfirmed = slot.status === 'CONFIRMED';
            return (
              <div
                key={slot.slot_key}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  backgroundColor: isConfirmed ? '#f0fdf4' : '#fffbeb',
                  border: `1px solid ${isConfirmed ? '#bbf7d0' : '#fef3c7'}`,
                  borderRadius: '10px',
                  padding: '6px 10px',
                  fontSize: '13px',
                }}
              >
                {isConfirmed ? (
                  <CheckCircle2 size={14} color="#16a34a" />
                ) : (
                  <HelpCircle size={14} color="#d97706" />
                )}
                <span style={{ fontWeight: 600, color: '#334155' }}>
                  {formatSlotKey(slot.slot_key)}:
                </span>
                <span style={{ fontWeight: 700, color: '#0f172a' }}>
                  {formatSlotValue(slot.canonical_value, slot.canonical_unit)}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Missing Slots Checklist */}
      {missingSlots.length > 0 && (
        <div style={{ fontSize: '12px', color: '#64748b', borderTop: '1px dashed #e2e8f0', paddingTop: '8px' }}>
          <span style={{ fontWeight: 600 }}>{kn.dialogue.missingInfo} </span>
          <span>{missingSlots.map(formatSlotKey).join(', ')}</span>
        </div>
      )}

      {/* Trigger Scheme Evaluation CTA */}
      {isEvaluationReady && (
        <div style={{ marginTop: '4px' }}>
          <Button
            onClick={onEvaluate}
            isLoading={isEvaluating}
            variant="accent"
            size="md"
            icon={<Sparkles size={18} />}
            style={{ width: '100%', fontWeight: 700 }}
          >
            {kn.dialogue.evaluateButton}
          </Button>
        </div>
      )}
    </div>
  );
};
