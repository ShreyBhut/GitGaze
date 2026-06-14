import { create } from 'zustand';
import { authApi } from '../lib/api';

interface User {
  id: string;
  username: string;
  avatar_url: string;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  checkAuth: () => Promise<void>;
  login: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  checkAuth: async () => {
    try {
      const user = await authApi.getMe();
      set({ user, isLoading: false });
    } catch {
      set({ user: null, isLoading: false });
    }
  },
  login: () => {
    window.location.href = 'http://localhost:8000/api/v1/auth/github/login';
  }
}));
