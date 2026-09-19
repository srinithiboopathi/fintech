import { create } from 'zustand';
import { User } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: {
    id: 'u-001',
    username: 'quant_trader',
    name: 'Alex Vance',
    email: 'alex.vance@quantlab.internal',
    role: 'Lead Quantitative Researcher',
    tier: 'Enterprise Institutional',
  },
  token: 'mock-session-jwt-token',
  isAuthenticated: true,
  login: (user, token) => {
    localStorage.setItem('quantlab_token', token);
    set({ user, token, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem('quantlab_token');
    set({ user: null, token: null, isAuthenticated: false });
  },
}));
