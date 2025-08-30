import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, ArrowRight } from 'lucide-react';

interface SuccessMessageProps {
  userType: 'customer' | 'seller';
  onContinue: () => void;
}

export const SuccessMessage = ({ userType, onContinue }: SuccessMessageProps) => {
  return (
    <Card className="w-full max-w-md card-shadow animate-scale-bounce">
      <CardHeader className="text-center">
        <div className="w-20 h-20 mx-auto bg-marketplace-success/10 rounded-full flex items-center justify-center mb-4">
          <CheckCircle className="w-10 h-10 text-marketplace-success" />
        </div>
        <CardTitle className="text-2xl font-bold text-foreground">
          Welcome to the Marketplace!
        </CardTitle>
        <p className="text-muted-foreground">
          {userType === 'seller' 
            ? 'Your seller account has been created successfully. Start listing your products!'
            : 'Your customer account is ready. Start exploring amazing products!'
          }
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="p-4 bg-marketplace-primary/5 rounded-lg border border-marketplace-primary/20">
            <h4 className="font-semibold text-foreground mb-2">Next Steps:</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              {userType === 'seller' ? (
                <>
                  <li>• Complete your seller profile</li>
                  <li>• Add your first product</li>
                  <li>• Set up payment methods</li>
                  <li>• Start receiving orders</li>
                </>
              ) : (
                <>
                  <li>• Explore product categories</li>
                  <li>• Add items to your wishlist</li>
                  <li>• Follow your favorite sellers</li>
                  <li>• Start shopping!</li>
                </>
              )}
            </ul>
          </div>

          <Button
            onClick={onContinue}
            variant={userType === 'seller' ? 'seller' : 'customer'}
            className="w-full h-12 group"
          >
            {userType === 'seller' ? 'Go to Dashboard' : 'Start Shopping'}
            <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};