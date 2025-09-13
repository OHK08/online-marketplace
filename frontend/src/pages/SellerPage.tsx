import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { NewPostForm } from '@/components/forms/NewPostForm';
import { InventoryTable } from '@/components/seller/InventoryTable';
import { Plus, Package, ShoppingCart, BarChart, Eye, MessageCircle } from 'lucide-react';
import { orderService } from '@/services/order';
import { Loader } from '@/components/ui/Loader';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';

interface SellerOrder {
  _id: string;
  buyerId: {
    _id: string;
    name: string;
    email: string;
  };
  items: Array<{
    artworkId: {
      _id: string;
      title: string;
      price: number;
      currency: string;
    };
    sellerId: string;
    qty: number;
    unitPrice: number;
    titleCopy: string;
  }>;
  total: number;
  currency: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

const SellerPage = () => {
  const [activeTab, setActiveTab] = useState('new-post');
  const [orders, setOrders] = useState<SellerOrder[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<SellerOrder | null>(null);
  const { toast } = useToast();

  // Mock stats data - you can replace with real API calls
  const stats = [
    {
      title: 'Total Products',
      value: '24', //change this to dynamic value
      icon: Package,
      description: '+2 from last month', //change this to dynamic value
    },
    {
      title: 'Total Orders',
      value: orders.length.toString(),
      icon: ShoppingCart,
      description: '+12 from last week', //change this to dynamic value
    },
    {
      title: 'Revenue',
      value: `₹${orders.reduce((sum, order) => sum + order.total, 0).toFixed(2)}`,
      icon: BarChart,
      description: '+8% from last month', //change this to dynamic value
    },
  ];

  useEffect(() => {
    if (activeTab === 'orders') {
      loadSellerOrders();
    }
  }, [activeTab]);

  const loadSellerOrders = async () => {
    try {
      setLoading(true);
      const response = await orderService.getSales();
      if (response.success && response.sales) {
        setOrders(response.sales);
      }
    } catch (error) {
      console.error('Error loading orders:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load orders.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (orderId: string, artworkId: string, newStatus: string) => {
    try {
      const response = await orderService.updateOrderStatus(orderId, { artworkId, status: newStatus });
      if (response.success) {
        // Update local state
        setOrders(orders.map(order => 
          order._id === orderId 
            ? { ...order, status: newStatus }
            : order
        ));
        toast({
          title: 'Success',
          description: 'Order status updated successfully.',
        });
      }
    } catch (error) {
      console.error('Error updating order status:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to update order status.',
      });
    }
  };

  const getCurrencySymbol = (currency: string) => {
    const symbols: { [key: string]: string } = {
      'INR': '₹',
      'USD': '$',
      'EUR': '€',
      'GBP': '£'
    };
    return symbols[currency] || currency;
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'delivered': return 'default';
      case 'shipped': return 'secondary';
      case 'paid': return 'outline';
      case 'created': return 'destructive';
      case 'cancelled': return 'destructive';
      default: return 'secondary';
    }
  };

  const OrdersTable = () => {
    if (loading) {
      return <Loader text="Loading orders..." />;
    }

    return (
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Order ID</TableHead>
            <TableHead>Buyer</TableHead>
            <TableHead>Items</TableHead>
            <TableHead>Amount</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {orders.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                No orders found. Your orders will appear here when customers purchase your items.
              </TableCell>
            </TableRow>
          ) : (
            orders.map((order) => (
              <TableRow key={order._id}>
                <TableCell className="font-medium">
                  {order._id.slice(-8).toUpperCase()}
                </TableCell>
                <TableCell>
                  <div>
                    <div className="font-medium">{order.buyerId.name}</div>
                    <div className="text-sm text-muted-foreground">{order.buyerId.email}</div>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="space-y-1">
                    {order.items.map((item, index) => (
                      <div key={index} className="text-sm">
                        {item.titleCopy} x{item.qty}
                      </div>
                    ))}
                  </div>
                </TableCell>
                <TableCell>
                  {getCurrencySymbol(order.currency)}{order.total.toFixed(2)}
                </TableCell>
                <TableCell>
                  <Badge variant={getStatusVariant(order.status)}>
                    {order.status.replace('_', ' ')}
                  </Badge>
                </TableCell>
                <TableCell>
                  {format(new Date(order.createdAt), 'MMM dd, yyyy')}
                </TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => setSelectedOrder(order)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl">
                        <DialogHeader>
                          <DialogTitle>Order Details</DialogTitle>
                        </DialogHeader>
                        {selectedOrder && (
                          <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <h4 className="font-semibold">Order Information</h4>
                                <p className="text-sm">Order ID: {selectedOrder._id}</p>
                                <p className="text-sm">Status: <Badge variant={getStatusVariant(selectedOrder.status)}>{selectedOrder.status}</Badge></p>
                                <p className="text-sm">Date: {format(new Date(selectedOrder.createdAt), 'MMM dd, yyyy HH:mm')}</p>
                              </div>
                              <div>
                                <h4 className="font-semibold">Buyer Information</h4>
                                <p className="text-sm">{selectedOrder.buyerId.name}</p>
                                <p className="text-sm">{selectedOrder.buyerId.email}</p>
                              </div>
                            </div>
                            <div>
                              <h4 className="font-semibold mb-2">Items</h4>
                              <div className="space-y-2">
                                {selectedOrder.items.map((item, index) => (
                                  <div key={index} className="flex justify-between items-center p-2 bg-muted rounded">
                                    <div>
                                      <p className="font-medium">{item.titleCopy}</p>
                                      <p className="text-sm text-muted-foreground">Quantity: {item.qty}</p>
                                    </div>
                                    <div className="text-right">
                                      <p className="font-medium">
                                        {getCurrencySymbol(selectedOrder.currency)}{item.unitPrice.toFixed(2)} each
                                      </p>
                                      <p className="text-sm text-muted-foreground">
                                        Total: {getCurrencySymbol(selectedOrder.currency)}{(item.unitPrice * item.qty).toFixed(2)}
                                      </p>
                                    </div>
                                  </div>
                                ))}
                              </div>
                              <div className="mt-4 pt-4 border-t">
                                <div className="flex justify-between items-center font-semibold">
                                  <span>Order Total:</span>
                                  <span>{getCurrencySymbol(selectedOrder.currency)}{selectedOrder.total.toFixed(2)}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </DialogContent>
                    </Dialog>
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Seller Dashboard</h1>
          <p className="text-muted-foreground">
            Manage your products, orders, and grow your business
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {stats.map((stat, index) => (
            <Card key={index} className="card-hover">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground">{stat.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="new-post" className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              New Post
            </TabsTrigger>
            <TabsTrigger value="stories">Stories</TabsTrigger>
            <TabsTrigger value="orders">Orders</TabsTrigger>
            <TabsTrigger value="inventory">Inventory</TabsTrigger>
          </TabsList>

          <TabsContent value="new-post" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Create New Product</CardTitle>
              </CardHeader>
              <CardContent>
                <NewPostForm />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="stories" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Stories</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12">
                  <h3 className="text-lg font-semibold mb-2">Stories Coming Soon</h3>
                  <p className="text-muted-foreground">
                    Share behind-the-scenes content and connect with your audience
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="orders" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Order Management</CardTitle>
              </CardHeader>
              <CardContent>
                <OrdersTable />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="inventory" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Product Inventory</CardTitle>
              </CardHeader>
              <CardContent>
                <InventoryTable />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default SellerPage;