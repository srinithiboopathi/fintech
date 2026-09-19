import { apiClient } from '../lib/api';
import {
  LoginPayload,
  RegisterPayload,
  AuthResponse,
  User,
  MessageResponse,
} from '../types';

export const authApi = {
  /**
   * Register a new user account and obtain access token
   */
  register: async (payload: RegisterPayload): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/register', payload);
    return response.data;
  },

  /**
   * Authenticate user credentials and obtain access token
   */
  login: async (payload: LoginPayload): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/login', payload);
    return response.data;
  },

  /**
   * Fetch profile for current authenticated user
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  /**
   * Session logout
   */
  logout: async (): Promise<MessageResponse> => {
    const response = await apiClient.post<MessageResponse>('/auth/logout');
    return response.data;
  },
};
