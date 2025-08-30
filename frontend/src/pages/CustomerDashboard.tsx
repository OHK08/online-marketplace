import { useState } from 'react';
import { Link } from 'react-router-dom';
import Footer from '../components/layout/footer';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  ShoppingBag, 
  Heart, 
  Search, 
  Filter, 
  Star,
  MapPin,
  User,
  LogOut,
  Bell,
  Settings
} from 'lucide-react';

const CustomerDashboard = () => {
  const [searchQuery, setSearchQuery] = useState('');

  // Mock data - replace with actual API calls
  const featuredProducts = [
    {
      id: 1,
      name: "Handcrafted Ceramic Vase",
      price: 89.99,
      seller: "ArtisanCrafts",
      rating: 4.8,
      image: "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400",
      location: "Brooklyn, NY",
      isWishlisted: false
    },
    {
      id: 2,
      name: "Organic Honey Collection",
      price: 24.99,
      seller: "BeeHappy Farm",
      rating: 4.9,
      image: "https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=400",
      location: "Vermont",
      isWishlisted: true
    },
    {
      id: 3,
      name: "Leather Journal",
      price: 45.00,
      seller: "CraftedGoods",
      rating: 4.7,
      image: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400",
      location: "Portland, OR",
      isWishlisted: false
    }
  ];

  const categories = [
    "Handmade Crafts",
    "Organic Food",
    "Vintage Items",
    "Art & Design",
    "Home Decor",
    "Jewelry"
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="text-2xl font-bold marketplace-gradient bg-clip-text text-transparent">
              MarketPlace
            </Link>
            
            {/* Search Bar */}
            <div className="flex-1 max-w-2xl mx-8">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search for products, sellers, or categories..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-marketplace-primary/20 focus:border-marketplace-primary"
                />
              </div>
            </div>

            {/* User Actions */}
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="icon">
                <Bell className="h-5 w-5" />
              </Button>
              <Button variant="ghost" size="icon">
                <Heart className="h-5 w-5" />
              </Button>
              <Button variant="ghost" size="icon">
                <ShoppingBag className="h-5 w-5" />
              </Button>
              <div className="flex items-center gap-2 ml-2">
                <Button variant="ghost" size="icon">
                  <User className="h-5 w-5" />
                </Button>
                <Button variant="ghost" size="icon">
                  <Settings className="h-5 w-5" />
                </Button>
                <Button variant="ghost" size="icon">
                  <LogOut className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Welcome back, Customer!</h1>
          <p className="text-muted-foreground">Discover amazing products from local artisans and sellers</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <Card className="card-shadow">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Filter className="h-5 w-5" />
                  Categories
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {categories.map((category, index) => (
                    <Button
                      key={index}
                      variant="ghost"
                      className="w-full justify-start text-left"
                    >
                      {category}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card className="card-shadow mt-6">
              <CardHeader>
                <CardTitle>Your Activity</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Wishlist Items</span>
                  <Badge variant="secondary">12</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Orders</span>
                  <Badge variant="secondary">8</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Reviews</span>
                  <Badge variant="secondary">15</Badge>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {/* Featured Products */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold">Featured Products</h2>
                <Button variant="outline">View All</Button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {featuredProducts.map((product) => (
                  <Card key={product.id} className="card-shadow hover:scale-105 transition-smooth cursor-pointer group">
                    <CardContent className="p-0">
                      <div className="relative">
                        <img
                          src={product.image}
                          alt={product.name}
                          className="w-full h-48 object-cover rounded-t-lg"
                        />
                        <Button
                          variant="ghost"
                          size="icon"
                          className="absolute top-2 right-2 bg-white/80 hover:bg-white"
                        >
                          <Heart className={`h-4 w-4 ${product.isWishlisted ? 'fill-marketplace-primary text-marketplace-primary' : ''}`} />
                        </Button>
                      </div>
                      
                      <div className="p-4">
                        <h3 className="font-semibold mb-2 group-hover:text-marketplace-primary transition-colors">
                          {product.name}
                        </h3>
                        
                        <div className="flex items-center gap-1 mb-2">
                          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                          <span className="text-sm font-medium">{product.rating}</span>
                          <span className="text-sm text-muted-foreground">• {product.seller}</span>
                        </div>
                        
                        <div className="flex items-center gap-1 mb-3 text-sm text-muted-foreground">
                          <MapPin className="h-3 w-3" />
                          {product.location}
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <span className="text-lg font-bold text-marketplace-primary">
                            ${product.price}
                          </span>
                          <Button variant="marketplace" size="sm">
                            Add to Cart
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* Recent Orders */}
            <Card className="card-shadow">
              <CardHeader>
                <CardTitle>Recent Orders</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-marketplace-primary/10 rounded-lg flex items-center justify-center">
                        <ShoppingBag className="h-6 w-6 text-marketplace-primary" />
                      </div>
                      <div>
                        <h4 className="font-medium">Handmade Pottery Set</h4>
                        <p className="text-sm text-muted-foreground">Order #MP2024001</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">$156.99</p>
                      <Badge variant="secondary">Delivered</Badge>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-marketplace-secondary/10 rounded-lg flex items-center justify-center">
                        <ShoppingBag className="h-6 w-6 text-marketplace-secondary" />
                      </div>
                      <div>
                        <h4 className="font-medium">Organic Skincare Bundle</h4>
                        <p className="text-sm text-muted-foreground">Order #MP2024002</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">$89.50</p>
                      <Badge variant="outline">In Transit</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default CustomerDashboard;