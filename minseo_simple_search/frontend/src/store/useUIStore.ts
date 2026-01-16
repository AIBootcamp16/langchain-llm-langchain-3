/**
 * UI Store
 * UI 상태 관리 스토어
 */

import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  modalOpen: boolean;
  modalContent: React.ReactNode | null;
  toast: { message: string; type: 'success' | 'error' | 'info' } | null;
  
  toggleSidebar: () => void;
  openModal: (content: React.ReactNode) => void;
  closeModal: () => void;
  showToast: (message: string, type?: 'success' | 'error' | 'info') => void;
  hideToast: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  modalOpen: false,
  modalContent: null,
  toast: null,
  
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  
  openModal: (content) => set({ modalOpen: true, modalContent: content }),
  
  closeModal: () => set({ modalOpen: false, modalContent: null }),
  
  showToast: (message, type = 'info') => set({ toast: { message, type } }),
  
  hideToast: () => set({ toast: null }),
}));

