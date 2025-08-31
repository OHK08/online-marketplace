import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Eye, MessageCircle } from 'lucide-react';

const mockOrders = [
  { id: 'ORD-001', buyer: 'John Doe', item: 'Ceramic Vase', amount: 89.99, status: 'delivered', date: '2024-01-20' },
  { id: 'ORD-002', buyer: 'Jane Smith', item: 'Leather Journal', amount: 45.00, status: 'shipped', date: '2024-01-18' },
  { id: 'ORD-003', buyer: 'Mike Wilson', item: 'Art Print', amount: 35.00, status: 'processing', date: '2024-01-15' },
];

export const OrdersTable = () => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'delivered': return 'bg-green-100 text-green-800';
      case 'shipped': return 'bg-blue-100 text-blue-800';
      case 'processing': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

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
        {mockOrders.map((order) => (
          <TableRow key={order.id}>
            <TableCell className="font-medium">{order.id}</TableCell>
            <TableCell>{order.buyer}</TableCell>
            <TableCell>{order.item}</TableCell>
            <TableCell>${order.amount}</TableCell>
            <TableCell>
              <Badge className={getStatusColor(order.status)}>
                {order.status}
              </Badge>
            </TableCell>
            <TableCell>{order.date}</TableCell>
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
        ))}
      </TableBody>
    </Table>
  );
};