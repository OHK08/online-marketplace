import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ShoppingBag, Store, Users, TrendingUp } from 'lucide-react';
import marketplaceHero from '@/assets/marketplace-hero.jpg';

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="w-full p-4 md:p-6 border-b">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="text-2xl font-bold marketplace-gradient bg-clip-text text-transparent">
            MarketPlace
          </div>
          <div className="flex items-center gap-4">
            <Link to="/signup">
              <Button variant="marketplace" className="hidden sm:inline-flex">
                Join Now
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="outline">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 marketplace-gradient opacity-10"></div>
        <div className="max-w-7xl mx-auto px-4 py-20 md:py-32">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8 animate-fade-slide-up">
              <h1 className="text-4xl md:text-6xl font-bold leading-tight">
                Your Local
                <span className="marketplace-gradient bg-clip-text text-transparent block">
                  Marketplace
                </span>
                Awaits
              </h1>
              <p className="text-xl text-muted-foreground max-w-lg">
                Connect with local artisans, discover unique products, and join a community 
                that celebrates creativity and entrepreneurship.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link to="/signup">
                  <Button variant="marketplace" size="lg" className="w-full sm:w-auto h-14 px-8">
                    <ShoppingBag className="w-5 h-5 mr-2" />
                    Start Shopping
                  </Button>
                </Link>
                <Link to="/signup">
                  <Button variant="seller" size="lg" className="w-full sm:w-auto h-14 px-8">
                    <Store className="w-5 h-5 mr-2" />
                    Start Selling
                  </Button>
                </Link>
              </div>
            </div>
            
            <div className="relative animate-fade-slide-up delay-200">
              <div className="relative rounded-2xl overflow-hidden card-shadow">
                <img
                  src={marketplaceHero}
                  alt="Marketplace Community"
                  className="w-full h-auto"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Why Choose Our Marketplace?
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              We're building more than just a platform - we're creating a community
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center p-6 card-gradient rounded-xl card-shadow transition-smooth hover:scale-105">
              <div className="w-16 h-16 mx-auto bg-marketplace-primary/10 rounded-full flex items-center justify-center mb-4">
                <Users className="w-8 h-8 text-marketplace-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Trusted Community</h3>
              <p className="text-muted-foreground">
                Join thousands of verified buyers and sellers in our secure marketplace
              </p>
            </div>

            <div className="text-center p-6 card-gradient rounded-xl card-shadow transition-smooth hover:scale-105">
              <div className="w-16 h-16 mx-auto bg-marketplace-secondary/10 rounded-full flex items-center justify-center mb-4">
                <TrendingUp className="w-8 h-8 text-marketplace-secondary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Growing Sales</h3>
              <p className="text-muted-foreground">
                Our sellers see average growth of 40% in their first three months
              </p>
            </div>

            <div className="text-center p-6 card-gradient rounded-xl card-shadow transition-smooth hover:scale-105">
              <div className="w-16 h-16 mx-auto bg-marketplace-accent/10 rounded-full flex items-center justify-center mb-4">
                <ShoppingBag className="w-8 h-8 text-marketplace-accent" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Unique Products</h3>
              <p className="text-muted-foreground">
                Discover one-of-a-kind items you won't find anywhere else
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto text-center px-4">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Whether you're looking to buy unique products or start your selling journey, 
            we're here to support you every step of the way.
          </p>
          <Link to="/signup">
            <Button variant="marketplace" size="lg" className="h-14 px-12">
              Join Our Marketplace
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-muted-foreground">
          <p>&copy; 2024 MarketPlace. Built with ❤️ for creators and entrepreneurs.</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
