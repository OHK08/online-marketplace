import { useState } from 'react';
import { toast } from '@/hooks/use-toast';

const API_BASE_URL = 'http://localhost:5000/auth';

interface SendOtpData {
  email: string;
}

interface SignupData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  phone: string;
  otp: string;
}

interface LoginData {
  email: string;
  password: string;
}

interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data?: T;
  user?: T;
  token?: string;
}

export const useAuth = () => {
  const [loading, setLoading] = useState(false);

  const sendOtp = async (data: SendOtpData): Promise<ApiResponse> => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/send-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const result = await response.json();
      if (!response.ok) throw new Error(result.message || 'Failed to send OTP');

      toast({
        title: "OTP Sent",
        description: "Check your email for the verification code",
      });

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send OTP';
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signup = async (data: SignupData): Promise<ApiResponse> => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const result = await response.json();
      if (!response.ok) throw new Error(result.message || 'Signup failed');

      toast({
        title: "Success",
        description: "Account created successfully!",
      });

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Signup failed';
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const login = async (data: LoginData): Promise<ApiResponse> => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const result = await response.json();
      if (!response.ok) throw new Error(result.message || 'Login failed');

      // Store token in localStorage
      if (result.token) {
        localStorage.setItem('authToken', result.token);
      }

      toast({
        title: "Success",
        description: "Logged in successfully!",
      });

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Fetch user profile (protected route)
  const getProfile = async (): Promise<ApiResponse> => {
    setLoading(true);
    try {
      const token = localStorage.getItem('authToken');
      if (!token) throw new Error("No authentication token found");

      const response = await fetch(`${API_BASE_URL}/profile`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const result = await response.json();
      if (!response.ok) throw new Error(result.message || 'Failed to fetch profile');

      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch profile';
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    sendOtp,
    signup,
    login,
    getProfile, // expose profile fetch
  };
};