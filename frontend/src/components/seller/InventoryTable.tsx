import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Edit, Eye, Trash } from 'lucide-react';

const mockInventory = [
  { id: '1', title: 'Ceramic Vase', price: 89.99, stock: 5, status: 'Published', likes: 24 },
  { id: '2', title: 'Leather Journal', price: 45.00, stock: 12, status: 'Published', likes: 18 },
  { id: '3', title: 'Art Print', price: 35.00, stock: 0, status: 'Draft', likes: 8 },
];

export const InventoryTable = () => {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Product</TableHead>
          <TableHead>Price</TableHead>
          <TableHead>Stock</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Likes</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {mockInventory.map((item) => (
          <TableRow key={item.id}>
            <TableCell className="font-medium">{item.title}</TableCell>
            <TableCell>${item.price}</TableCell>
            <TableCell>{item.stock}</TableCell>
            <TableCell>
              <Badge variant={item.status === 'Published' ? 'default' : 'secondary'}>
                {item.status}
              </Badge>
            </TableCell>
            <TableCell>{item.likes}</TableCell>
            <TableCell>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm">
                  <Eye className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <Edit className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <Trash className="w-4 h-4" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};