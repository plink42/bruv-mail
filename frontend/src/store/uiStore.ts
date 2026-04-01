import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIStore {
  apiToken: string | null;
  setApiToken: (token: string | null) => void;
  selectedTag: string | null;
  setSelectedTag: (tag: string | null) => void;
  selectedAccountId: number | null;
  setSelectedAccountId: (id: number | null) => void;
  currentPage: number;
  setCurrentPage: (page: number) => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      apiToken: null,
      setApiToken: (token) => set({ apiToken: token }),
      selectedTag: null,
      setSelectedTag: (tag) => set({ selectedTag: tag }),
      selectedAccountId: null,
      setSelectedAccountId: (id) => set({ selectedAccountId: id }),
      currentPage: 0,
      setCurrentPage: (page) => set({ currentPage: page }),
    }),
    {
      name: 'ui-store',
      partialize: (state) => ({
        selectedTag: state.selectedTag,
        selectedAccountId: state.selectedAccountId,
        currentPage: state.currentPage,
      }),
    }
  )
);
