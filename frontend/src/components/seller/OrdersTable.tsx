import { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Eye, MessageCircle } from 'lucide-react';
import { orderService, type Order } from '@/services/order';
import { useToast } from '@/hooks/use-toast';
import { Loader } from '@/components/ui/Loader';
import { format } from 'date-fns';

export const OrdersTable = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const loadSellerOrders = async () => {
      try {
        const response = await orderService.getSellerOrders();
        if (response.success && response.orders) {
          setOrders(response.orders);
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

    loadSellerOrders();
  }, [toast]);

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
      case 'processing': return 'outline';
      case 'pending': return 'destructive';
      default: return 'secondary';
    }
  };

  if (loading) {
    return <Loader text="Loading orders..." />;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Order ID</TableHead>
          <TableHead>Buyer</TableHead>
          <TableHead>Item</TableHead>
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
              <TableCell className="font-medium">{order._id.slice(-8).toUpperCase()}</TableCell>
              <TableCell>{order.buyerId.name}</TableCell>
              <TableCell>{order.artworkId.title}</TableCell>
              <TableCell>
                {getCurrencySymbol(order.artworkId.currency)}{order.totalAmount}
              </TableCell>
              <TableCell>
                <Badge variant={getStatusVariant(order.status)}>
                  {order.status}
                </Badge>
              </TableCell>
              <TableCell>{format(new Date(order.createdAt), 'MMM dd, yyyy')}</TableCell>
              <TableCell>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm">
                    <Eye className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <MessageCircle className="w-4 h-4" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
};