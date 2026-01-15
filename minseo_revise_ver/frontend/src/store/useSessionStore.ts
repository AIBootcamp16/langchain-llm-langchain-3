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
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      sessionId: null,
      setSessionId: (id: string) => set({ sessionId: id }),
      clearSession: () => set({ sessionId: null }),
    }),
    {
      name: 'session-storage',
    }
  )
);

