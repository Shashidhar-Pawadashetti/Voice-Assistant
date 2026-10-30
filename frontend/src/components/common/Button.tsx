import React from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'danger' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg' | 'giant';
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  className = '',
  disabled,
  style,
  ...props
}) => {
  const baseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    borderRadius: '12px',
    fontWeight: 600,
    cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
    opacity: disabled || isLoading ? 0.65 : 1,
    border: 'none',
    transition: 'all 0.15s ease',
    textDecoration: 'none',
    touchAction: 'manipulation',
    ...style,
  };

  const sizeStyles: Record<string, React.CSSProperties> = {
    sm: { padding: '8px 14px', fontSize: '14px', minHeight: '38px' },
    md: { padding: '12px 20px', fontSize: '16px', minHeight: '48px' },
    lg: { padding: '14px 24px', fontSize: '18px', minHeight: '54px' },
    giant: { padding: '20px 32px', fontSize: '20px', minHeight: '68px', borderRadius: '24px' },
  };

  const variantStyles: Record<string, React.CSSProperties> = {
    primary: { backgroundColor: '#1b4d3e', color: '#ffffff' },
    secondary: { backgroundColor: '#2d6a4f', color: '#ffffff' },
    accent: { backgroundColor: '#e9c46a', color: '#1a202c' },
    danger: { backgroundColor: '#d90429', color: '#ffffff' },
    outline: { backgroundColor: 'transparent', color: '#1b4d3e', border: '2px solid #1b4d3e' },
    ghost: { backgroundColor: 'transparent', color: '#2d6a4f' },
  };

  return (
    <button
      disabled={disabled || isLoading}
      style={{
        ...baseStyle,
        ...sizeStyles[size],
        ...variantStyles[variant],
      }}
      className={className}
      {...props}
    >
      {isLoading ? <Loader2 className="spinner" size={20} /> : icon}
      <span>{children}</span>
    </button>
  );
};
