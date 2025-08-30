import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Eye, EyeOff, Mail, User, Phone, Lock } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

interface SignupFormProps {
  userType: 'customer' | 'seller';
  onSuccess: () => void;
  onBack: () => void;
}

export const SignupForm = ({ userType, onSuccess, onBack }: SignupFormProps) => {
  const [step, setStep] = useState<'details' | 'otp'>('details');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    phone: '',
    otp: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { loading, sendOtp, signup } = useAuth();

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.email.trim()) newErrors.email = 'Email is required';
    if (!/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = 'Email is invalid';
    if (!formData.password) newErrors.password = 'Password is required';
    if (formData.password.length < 6) newErrors.password = 'Password must be at least 6 characters';
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    if (!formData.phone.trim()) newErrors.phone = 'Phone number is required';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    try {
      await sendOtp({ email: formData.email });
      setStep('otp');
    } catch (error) {
      console.error('Failed to send OTP:', error);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.otp.trim()) {
      setErrors({ otp: 'OTP is required' });
      return;
    }

    try {
      await signup(formData);
      onSuccess();
    } catch (error) {
      console.error('Signup failed:', error);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  if (step === 'otp') {
    return (
      <Card className="w-full max-w-md card-shadow animate-fade-slide-up">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-foreground">
            Verify Your Email
          </CardTitle>
          <p className="text-muted-foreground">
            We've sent a verification code to {formData.email}
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSignup} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="otp">Verification Code</Label>
              <Input
                id="otp"
                type="text"
                placeholder="Enter 6-digit code"
                value={formData.otp}
                onChange={(e) => handleInputChange('otp', e.target.value)}
                className="input-focus text-center text-lg tracking-widest"
                maxLength={6}
              />
              {errors.otp && <p className="text-sm text-marketplace-error">{errors.otp}</p>}
            </div>

            <div className="space-y-3">
              <Button
                type="submit"
                variant={userType === 'seller' ? 'seller' : 'customer'}
                className="w-full h-12"
                disabled={loading}
              >
                {loading ? 'Creating Account...' : 'Create Account'}
              </Button>
              
              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={() => setStep('details')}
              >
                Back to Details
              </Button>
            </div>

            <div className="text-center">
              <Button
                type="button"
                variant="link"
                className="text-sm text-marketplace-primary"
                onClick={() => sendOtp({ email: formData.email })}
                disabled={loading}
              >
                Resend Code
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md card-shadow animate-fade-slide-up">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold text-foreground">
          Sign Up as {userType === 'seller' ? 'Seller' : 'Customer'}
        </CardTitle>
        <p className="text-muted-foreground">
          {userType === 'seller' 
            ? 'Start your journey as a marketplace seller' 
            : 'Join our community of shoppers'
          }
        </p>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSendOtp} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Full Name</Label>
            <div className="relative">
              <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                id="name"
                type="text"
                placeholder="Enter your full name"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="pl-10 input-focus"
              />
            </div>
            {errors.name && <p className="text-sm text-marketplace-error">{errors.name}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                className="pl-10 input-focus"
              />
            </div>
            {errors.email && <p className="text-sm text-marketplace-error">{errors.email}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">Phone Number</Label>
            <div className="relative">
              <Phone className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                id="phone"
                type="tel"
                placeholder="Enter your phone number"
                value={formData.phone}
                onChange={(e) => handleInputChange('phone', e.target.value)}
                className="pl-10 input-focus"
              />
            </div>
            {errors.phone && <p className="text-sm text-marketplace-error">{errors.phone}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Create a password"
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                className="pl-10 pr-10 input-focus"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-muted-foreground hover:text-foreground transition-smooth"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {errors.password && <p className="text-sm text-marketplace-error">{errors.password}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                id="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="Confirm your password"
                value={formData.confirmPassword}
                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                className="pl-10 pr-10 input-focus"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-3 text-muted-foreground hover:text-foreground transition-smooth"
              >
                {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {errors.confirmPassword && <p className="text-sm text-marketplace-error">{errors.confirmPassword}</p>}
          </div>

          <div className="space-y-3 pt-2">
            <Button
              type="submit"
              variant={userType === 'seller' ? 'seller' : 'customer'}
              className="w-full h-12"
              disabled={loading}
            >
              {loading ? 'Sending OTP...' : 'Continue'}
            </Button>
            
            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={onBack}
            >
              Back to Selection
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};