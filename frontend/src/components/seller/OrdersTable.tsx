import { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Eye } from 'lucide-react';
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
      case 'delivered':
        return 'default';
      case 'shipped':
      case 'out_for_delivery':
        return 'secondary';
      case 'paid':
      case 'created':
        return 'outline';
      case 'pending':
      case 'failed':
      case 'cancelled':
        return 'destructive';
      default:
        return 'secondary';
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
              <TableCell className="font-medium">{order._id.slice(-8).toUpperCase()}</TableCell>
              <TableCell>{order.buyerId.name}</TableCell>
              <TableCell>
                {order.items.map((item) => item.titleCopy).join(', ')}
              </TableCell>
              <TableCell>
                {getCurrencySymbol(order.currency)}{order.total.toFixed(2)}
              </TableCell>
              <TableCell>
                <Badge variant={getStatusVariant(order.status)}>
                  {order.status.replace('_', ' ')}
                </Badge>
              </TableCell>
              <TableCell>{format(new Date(order.createdAt), 'MMM dd, yyyy')}</TableCell>
              <TableCell>
                <Button variant="ghost" size="sm" onClick={() => window.location.href = `/orders/${order._id}`}>
                  <Eye className="w-4 h-4" />
                </Button>
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
};