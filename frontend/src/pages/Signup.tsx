import { useState } from 'react';
import { Link } from 'react-router-dom';
import { UserTypeSelector } from '@/components/signup/UserTypeSelector';
import { SignupForm } from '@/components/signup/SignupForm';
import { SuccessMessage } from '@/components/signup/SuccessMessage';
import { Button } from '@/components/ui/button';
import marketplaceHero from '@/assets/marketplace-hero.jpg';

type SignupStep = 'userType' | 'form' | 'success';

const Signup = () => {
  const [step, setStep] = useState<SignupStep>('userType');
  const [userType, setUserType] = useState<'customer' | 'seller' | null>(null);

  const handleTypeSelect = (type: 'customer' | 'seller') => {
    setUserType(type);
    setStep('form');
  };

  const handleSignupSuccess = () => {
    setStep('success');
  };

  const handleBackToSelection = () => {
    setStep('userType');
    setUserType(null);
  };

  const handleContinue = () => {
    // Navigate to dashboard or homepage based on user type
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="w-full p-4 md:p-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="text-2xl font-bold marketplace-gradient bg-clip-text text-transparent">
            MarketPlace
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost" className="text-muted-foreground hover:text-foreground">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex">
        {/* Left Side - Hero Image (Hidden on mobile) */}
        <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
          <div className="absolute inset-0 marketplace-gradient opacity-90"></div>
          <img
            src={marketplaceHero}
            alt="Marketplace Community"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 flex items-center justify-center p-12">
            <div className="text-center text-white space-y-6 animate-fade-slide-up">
              <h1 className="text-4xl xl:text-5xl font-bold leading-tight">
                Join Our Growing
                <br />
                <span className="text-marketplace-accent">Marketplace Community</span>
              </h1>
              <p className="text-xl text-white/90 max-w-md">
                Connect with thousands of buyers and sellers in our vibrant online marketplace
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold">10K+</div>
                  <div className="text-sm text-white/80">Active Users</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold">5K+</div>
                  <div className="text-sm text-white/80">Products</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold">500+</div>
                  <div className="text-sm text-white/80">Sellers</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Signup Form */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-6 md:p-12">
          <div className="w-full max-w-md">
            {step === 'userType' && (
              <UserTypeSelector
                selectedType={userType}
                onTypeSelect={handleTypeSelect}
              />
            )}

            {step === 'form' && userType && (
              <SignupForm
                userType={userType}
                onSuccess={handleSignupSuccess}
                onBack={handleBackToSelection}
              />
            )}

            {step === 'success' && userType && (
              <SuccessMessage
                userType={userType}
                onContinue={handleContinue}
              />
            )}

            {/* Footer Links */}
            <div className="mt-8 text-center text-sm text-muted-foreground">
              <p>
                By signing up, you agree to our{' '}
                <Link to="/terms" className="text-marketplace-primary hover:underline">
                  Terms of Service
                </Link>{' '}
                and{' '}
                <Link to="/privacy" className="text-marketplace-primary hover:underline">
                  Privacy Policy
                </Link>
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Signup;