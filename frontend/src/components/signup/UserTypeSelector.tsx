import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ShoppingBag, Store } from 'lucide-react';

interface UserTypeSelectorProps {
  selectedType: 'customer' | 'seller' | null;
  onTypeSelect: (type: 'customer' | 'seller') => void;
}

export const UserTypeSelector = ({ selectedType, onTypeSelect }: UserTypeSelectorProps) => {
  return (
    <div className="space-y-6 animate-fade-slide-up">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-foreground mb-2">Join Our Marketplace</h2>
        <p className="text-muted-foreground">Choose how you'd like to get started</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card
          className={`p-6 cursor-pointer transition-smooth hover:scale-105 card-shadow ${
            selectedType === 'customer'
              ? 'ring-2 ring-marketplace-secondary bg-marketplace-secondary/5'
              : 'hover:shadow-lg'
          }`}
          onClick={() => onTypeSelect('customer')}
        >
          <div className="text-center space-y-4">
            <div className="w-16 h-16 mx-auto bg-marketplace-secondary/10 rounded-full flex items-center justify-center">
              <ShoppingBag className="w-8 h-8 text-marketplace-secondary" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">Customer</h3>
              <p className="text-sm text-muted-foreground">
                Discover and purchase unique products from local artisans
              </p>
            </div>
            <Button
              variant={selectedType === 'customer' ? 'customer' : 'outline'}
              className="w-full"
            >
              Shop Products
            </Button>
          </div>
        </Card>

        <Card
          className={`p-6 cursor-pointer transition-smooth hover:scale-105 card-shadow ${
            selectedType === 'seller'
              ? 'ring-2 ring-marketplace-primary bg-marketplace-primary/5'
              : 'hover:shadow-lg'
          }`}
          onClick={() => onTypeSelect('seller')}
        >
          <div className="text-center space-y-4">
            <div className="w-16 h-16 mx-auto bg-marketplace-primary/10 rounded-full flex items-center justify-center">
              <Store className="w-8 h-8 text-marketplace-primary" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">Seller</h3>
              <p className="text-sm text-muted-foreground">
                Start selling your products and reach thousands of customers
              </p>
            </div>
            <Button
              variant={selectedType === 'seller' ? 'seller' : 'outline'}
              className="w-full"
            >
              Start Selling
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};