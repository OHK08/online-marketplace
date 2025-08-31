import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Package, Search, Eye, MessageCircle } from 'lucide-react';
import { EmptyState } from '@/components/ui/EmptyState';
import { format } from 'date-fns';

interface Order {
  id: string;
  item: {
    title: string;
    image: string;
    price: number;
  };
  seller: {
    name: string;
    avatar: string;
  };
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  orderDate: string;
  deliveryDate?: string;
  total: number;
}

const mockOrders: Order[] = [
  {
    id: 'ORD-001',
    item: {
      title: 'Handcrafted Ceramic Vase',
      image: 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=150',
      price: 89.99,
    },
    seller: {
      name: 'Sarah Johnson',
      avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b714?w=100',
    },
    status: 'delivered',
    orderDate: '2024-01-15',
    deliveryDate: '2024-01-20',
    total: 89.99,
  },
  {
    id: 'ORD-002',
    item: {
      title: 'Vintage Leather Journal',
      image: 'https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=150',
      price: 45.00,
    },
    seller: {
      name: 'Michael Chen',
      avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100',
    },
    status: 'shipped',
    orderDate: '2024-01-18',
    total: 45.00,
  },
  {
    id: 'ORD-003',
    item: {
      title: 'Artisan Coffee Beans',
      image: 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=150',
      price: 24.99,
    },
    seller: {
      name: 'Coffee Roasters Co.',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100',
    },
    status: 'processing',
    orderDate: '2024-01-20',
    total: 24.99,
  },
];

const OrderHistoryPage = () => {
  const [orders] = useState<Order[]>(mockOrders);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const getStatusColor = (status: Order['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
      case 'processing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
      case 'shipped':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300';
      case 'delivered':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      case 'cancelled':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  const filteredOrders = orders.filter(order => {
    const matchesSearch = order.item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         order.seller.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         order.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (orders.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <EmptyState
            icon={Package}
            title="No Orders Yet"
            description="Start shopping to see your order history here"
            action={{
              label: "Browse Products",
              onClick: () => window.location.href = "/dashboard"
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Order History</h1>
          <p className="text-muted-foreground">
            Track and manage all your purchases
          </p>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <Input
                  placeholder="Search orders..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full md:w-48">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Orders</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="processing">Processing</SelectItem>
                  <SelectItem value="shipped">Shipped</SelectItem>
                  <SelectItem value="delivered">Delivered</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Orders List */}
        <div className="space-y-4">
          {filteredOrders.map((order) => (
            <Card key={order.id} className="card-hover">
              <CardContent className="pt-6">
                <div className="flex flex-col lg:flex-row gap-6">
                  {/* Order Image */}
                  <div className="flex-shrink-0">
                    <img
                      src={order.item.image}
                      alt={order.item.title}
                      className="w-24 h-24 object-cover rounded-lg"
                    />
                  </div>

                  {/* Order Details */}
                  <div className="flex-1 space-y-2">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                      <h3 className="font-semibold text-lg">{order.item.title}</h3>
                      <Badge className={getStatusColor(order.status)}>
                        {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <span>Order #{order.id}</span>
                      <span>•</span>
                      <span>Ordered {format(new Date(order.orderDate), 'MMM dd, yyyy')}</span>
                      {order.deliveryDate && (
                        <>
                          <span>•</span>
                          <span>Delivered {format(new Date(order.deliveryDate), 'MMM dd, yyyy')}</span>
                        </>
                      )}
                    </div>

                    <div className="flex items-center gap-3">
                      <Avatar className="h-6 w-6">
                        <AvatarImage src={order.seller.avatar} alt={order.seller.name} />
                        <AvatarFallback className="text-xs">
                          {order.seller.name.charAt(0)}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-sm text-muted-foreground">
                        Sold by {order.seller.name}
                      </span>
                    </div>

                    <div className="text-lg font-semibold">
                      ${order.total.toFixed(2)}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-row lg:flex-col gap-2">
                    <Button variant="outline" size="sm" className="flex items-center gap-2">
                      <Eye className="w-4 h-4" />
                      View Details
                    </Button>
                    <Button variant="outline" size="sm" className="flex items-center gap-2">
                      <MessageCircle className="w-4 h-4" />
                      Contact Seller
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {filteredOrders.length === 0 && orders.length > 0 && (
          <EmptyState
            icon={Search}
            title="No Orders Found"
            description="Try adjusting your search or filter criteria"
          />
        )}
      </div>
    </div>
  );
};

export default OrderHistoryPage;