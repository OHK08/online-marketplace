import { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Edit, Eye, Trash } from 'lucide-react';
import { artworkService, type Artwork } from '@/services/artwork';
import { useToast } from '@/hooks/use-toast';
import { Loader } from '@/components/ui/Loader';

export const InventoryTable = () => {
  const [artworks, setArtworks] = useState<Artwork[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const loadMyArtworks = async () => {
      try {
        const response = await artworkService.getMyArtworks();
        if (response.success && response.artworks) {
          setArtworks(response.artworks);
        }
      } catch (error) {
        console.error('Error loading artworks:', error);
        toast({
          variant: 'destructive',
          title: 'Error',
          description: 'Failed to load your artworks.',
        });
      } finally {
        setLoading(false);
      }
    };

    loadMyArtworks();
  }, [toast]);

  const handleDelete = async (id: string) => {
    try {
      await artworkService.deleteArtwork(id);
      setArtworks(artworks.filter(artwork => artwork._id !== id));
      toast({
        title: 'Success',
        description: 'Artwork deleted successfully.',
      });
    } catch (error) {
      console.error('Error deleting artwork:', error);
      toast({
        variant: 'destructive', 
        title: 'Error',
        description: 'Failed to delete artwork.',
      });
    }
  };

  if (loading) {
    return <Loader text="Loading your products..." />;
  }
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Product</TableHead>
          <TableHead>Price</TableHead>
          <TableHead>Quantity</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Likes</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {artworks.length === 0 ? (
          <TableRow>
            <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
              No products found. Create your first product!
            </TableCell>
          </TableRow>
        ) : (
          artworks.map((artwork) => (
            <TableRow key={artwork._id}>
              <TableCell className="font-medium">{artwork.title}</TableCell>
              <TableCell>₹{artwork.price}</TableCell>
              <TableCell>{artwork.quantity}</TableCell>
              <TableCell>
                <Badge variant={artwork.status === 'published' ? 'default' : 'secondary'}>
                  {artwork.status}
                </Badge>
              </TableCell>
              <TableCell>{artwork.likeCount}</TableCell>
              <TableCell>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm">
                    <Eye className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => handleDelete(artwork._id)}
                  >
                    <Trash className="w-4 h-4" />
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