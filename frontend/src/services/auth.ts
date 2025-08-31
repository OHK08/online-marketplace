import apiClient from '@/lib/axios';

export interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  bio?: string;
  avatarUrl?: string;
  createdAt: string;
  updatedAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupPayload {
  name: string;
  phone: string;
  email: string;
  password: string;
  bio?: string;
  avatarUrl?: string;
  otp: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface SendOtpPayload {
  email: string;
}

export interface SendOtpResponse {
  message: string;
}

export const authService = {
  async sendOtp(payload: SendOtpPayload): Promise<SendOtpResponse> {
    const response = await apiClient.post('/auth/send-otp', payload);
    return response.data;
  },

  async signup(payload: SignupPayload): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/signup', payload);
    return response.data;
  },

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await apiClient.post('/auth/login', credentials);
    return response.data;
  },

  async getProfile(): Promise<{ user: User }> {
    const response = await apiClient.get('/auth/profile');
    return response.data;
  },
};