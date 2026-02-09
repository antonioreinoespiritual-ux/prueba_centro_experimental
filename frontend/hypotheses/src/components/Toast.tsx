import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

interface ToastState {
  message: string;
  tone?: 'success' | 'error' | 'info';
}

interface ToastContextValue {
  toast: ToastState | null;
  showToast: (message: string, tone?: ToastState['tone']) => void;
  clearToast: () => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toast, setToast] = useState<ToastState | null>(null);

  const showToast = useCallback((message: string, tone: ToastState['tone'] = 'info') => {
    setToast({ message, tone });
    window.setTimeout(() => setToast(null), 3000);
  }, []);

  const clearToast = useCallback(() => setToast(null), []);

  const value = useMemo(() => ({ toast, showToast, clearToast }), [toast, showToast, clearToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {toast && <div className="hyp-toast">{toast.message}</div>}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return ctx;
}
