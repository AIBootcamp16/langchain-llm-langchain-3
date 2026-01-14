/**
 * Session Store
 * 세션 관리 스토어
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SessionState {
  sessionId: string | null;
  setSessionId: (id: string) => void;
  clearSession: () => void;
  generateSessionId: () => string;
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      sessionId: null,
      setSessionId: (id: string) => set({ sessionId: id }),
      clearSession: () => set({ sessionId: null }),
      generateSessionId: () => {
        // Generate UUID v4
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
          const r = Math.random() * 16 | 0;
          const v = c === 'x' ? r : (r & 0x3 | 0x8);
          return v.toString(16);
        });
      },
    }),
    {
      name: 'session-storage',
    }
  )
);

