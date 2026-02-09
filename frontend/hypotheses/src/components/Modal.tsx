import React, { useEffect, useRef } from 'react';

const focusableSelector = [
  'a[href]',
  'button:not([disabled])',
  'textarea:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',');

interface ModalProps {
  open: boolean;
  onClose: () => void;
  ariaLabelledBy?: string;
  children: React.ReactNode;
}

export function Modal({ open, onClose, ariaLabelledBy, children }: ModalProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return undefined;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const content = contentRef.current;
    const focusable = content?.querySelectorAll<HTMLElement>(focusableSelector);
    const first = focusable?.[0];
    const last = focusable?.[focusable.length - 1];

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
        return;
      }
      if (event.key === 'Tab' && focusable && first && last) {
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    window.setTimeout(() => {
      if (first) {
        first.focus();
      } else if (content) {
        content.focus();
      }
    }, 0);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="hyp-modal-backdrop" role="presentation" onClick={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <div
        className="hyp-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={ariaLabelledBy}
        ref={contentRef}
        tabIndex={-1}
      >
        {children}
      </div>
    </div>
  );
}
