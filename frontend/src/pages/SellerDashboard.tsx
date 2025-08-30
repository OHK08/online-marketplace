import { useState } from 'react';
import { Link } from 'react-router-dom';
import Footer from '../components/layout/footer';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Plus,
  Package,
  TrendingUp,
  DollarSign,
  Eye,
  Edit,
  Users,
  Star,
  ShoppingCart,
  User,
  LogOut,
  Bell,
  Settings,
  BarChart3
} from 'lucide-react';

const SellerDashboard = () => {
  // Mock data - replace with actual API calls
  const stats = {
    totalProducts: 24,
    totalOrders: 156,
    totalRevenue: 12450.75,
    totalCustomers: 89,
    avgRating: 4.8
  };

  const recentProducts = [
    {
      id: 1,
      name: "Handcrafted Ceramic Vase",
      price: 89.99,
      stock: 12,
      orders: 23,
      image: "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=200",
      status: "active"
    },
    {
      id: 2,
      name: "Organic Honey Collection",
      price: 24.99,
      stock: 5,
      orders: 45,
      image: "https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=200",
      status: "low_stock"
    },
    {
      id: 3,
      name: "Leather Journal",
      price: 45.00,
      stock: 0,
      orders: 12,
      image: "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=200",
      status: "out_of_stock"
    }
  ];

  const recentOrders = [
    {
      id: "MP2024001",
      customer: "John Smith",
      product: "Handcrafted Ceramic Vase",
      amount: 89.99,
      status: "pending",
      date: "2024-01-15"
    },
    {
      id: "MP2024002",
      customer: "Sarah Johnson",
      product: "Organic Honey Collection",
      amount: 24.99,
      status: "shipped",
      date: "2024-01-14"
    },
    {
      id: "MP2024003",
      customer: "Mike Wilson",
      product: "Leather Journal",
      amount: 45.00,
      status: "delivered",
      date: "2024-01-13"
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600';
      case 'low_stock': return 'text-yellow-600';
      case 'out_of_stock': return 'text-red-600';
      case 'pending': return 'text-yellow-600';
      case 'shipped': return 'text-blue-600';
      case 'delivered': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active': return <Badge className="bg-green-100 text-green-800">Active</Badge>;
      case 'low_stock': return <Badge className="bg-yellow-100 text-yellow-800">Low Stock</Badge>;
      case 'out_of_stock': return <Badge className="bg-red-100 text-red-800">Out of Stock</Badge>;
      case 'pending': return <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>;
      case 'shipped': return <Badge className="bg-blue-100 text-blue-800">Shipped</Badge>;
      case 'delivered': return <Badge className="bg-green-100 text-green-800">Delivered</Badge>;
      default: return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="text-2xl font-bold marketplace-gradient bg-clip-text text-transparent">
              MarketPlace
            </Link>
            
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Seller Dashboard</span>
            </div>

            {/* User Actions */}
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="icon">
                <Bell className="h-5 w-5" />
              </Button>
              <Button variant="ghost" size="icon">
                <BarChart3 className="h-5 w-5" />
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
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Seller Dashboard</h1>
            <p className="text-muted-foreground">Manage your products and track your sales</p>
          </div>
          <Button variant="seller" className="h-12 px-6">
            <Plus className="h-5 w-5 mr-2" />
            Add New Product
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <Card className="card-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Products</p>
                  <p className="text-2xl font-bold">{stats.totalProducts}</p>
                </div>
                <Package className="h-8 w-8 text-marketplace-primary" />
              </div>
            </CardContent>
          </Card>

          <Card className="card-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Orders</p>
                  <p className="text-2xl font-bold">{stats.totalOrders}</p>
                </div>
                <ShoppingCart className="h-8 w-8 text-marketplace-secondary" />
              </div>
            </CardContent>
          </Card>

          <Card className="card-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Total Revenue</p>
                  <p className="text-2xl font-bold">${stats.totalRevenue.toLocaleString()}</p>
                </div>
                <DollarSign className="h-8 w-8 text-marketplace-accent" />
              </div>
            </CardContent>
          </Card>

          <Card className="card-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Customers</p>
                  <p className="text-2xl font-bold">{stats.totalCustomers}</p>
                </div>
                <Users className="h-8 w-8 text-marketplace-primary" />
              </div>
            </CardContent>
          </Card>

          <Card className="card-shadow">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Avg Rating</p>
                  <p className="text-2xl font-bold flex items-center gap-1">
                    {stats.avgRating}
                    <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Products */}
          <Card className="card-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Your Products</CardTitle>
                <Button variant="outline" size="sm">View All</Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentProducts.map((product) => (
                  <div key={product.id} className="flex items-center gap-4 p-4 border rounded-lg">
                    <img
                      src={product.image}
                      alt={product.name}
                      className="w-16 h-16 object-cover rounded-lg"
                    />
                    <div className="flex-1">
                      <h4 className="font-medium">{product.name}</h4>
                      <p className="text-sm text-muted-foreground">
                        ${product.price} • {product.orders} orders
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs">Stock: {product.stock}</span>
                        {getStatusBadge(product.status)}
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="icon">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon">
                        <Edit className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent Orders */}
          <Card className="card-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Recent Orders</CardTitle>
                <Button variant="outline" size="sm">View All</Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentOrders.map((order) => (
                  <div key={order.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <h4 className="font-medium">#{order.id}</h4>
                      <p className="text-sm text-muted-foreground">{order.customer}</p>
                      <p className="text-sm text-muted-foreground">{order.product}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">${order.amount}</p>
                      <p className="text-sm text-muted-foreground">{order.date}</p>
                      {getStatusBadge(order.status)}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="card-shadow mt-6">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Button variant="outline" className="h-20 flex-col gap-2">
                <Plus className="h-6 w-6" />
                Add Product
              </Button>
              <Button variant="outline" className="h-20 flex-col gap-2">
                <Package className="h-6 w-6" />
                Manage Inventory
              </Button>
              <Button variant="outline" className="h-20 flex-col gap-2">
                <BarChart3 className="h-6 w-6" />
                View Analytics
              </Button>
              <Button variant="outline" className="h-20 flex-col gap-2">
                <Settings className="h-6 w-6" />
                Store Settings
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
      <Footer />
    </div>
  );
};

export default SellerDashboard;