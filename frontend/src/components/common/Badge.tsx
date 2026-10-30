import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'demo' | 'neutral';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
}) => {
  const variantStyles: Record<string, React.CSSProperties> = {
    success: { backgroundColor: '#e8f5e9', color: '#2e7d32', border: '1px solid #c8e6c9' },
    warning: { backgroundColor: '#fff8e1', color: '#f57f17', border: '1px solid #ffe082' },
    danger: { backgroundColor: '#ffebee', color: '#c62828', border: '1px solid #ffcdd2' },
    info: { backgroundColor: '#e1f5fe', color: '#0277bd', border: '1px solid #b3e5fc' },
    demo: {
      backgroundColor: '#fbe9e7',
      color: '#d84315',
      border: '2px dashed #ff5722',
      fontWeight: 700,
      letterSpacing: '0.5px',
    },
    neutral: { backgroundColor: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0' },
  };

  const sizeStyles: Record<string, React.CSSProperties> = {
    sm: { padding: '2px 8px', fontSize: '12px' },
    md: { padding: '4px 12px', fontSize: '13px' },
  };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        borderRadius: '9999px',
        fontWeight: 600,
        ...sizeStyles[size],
        ...variantStyles[variant],
      }}
    >
      {children}
    </span>
  );
};
