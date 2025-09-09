import { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Edit, Trash, Package } from 'lucide-react';
import { artworkService, type Artwork } from '@/services/artwork';
import { useToast } from '@/hooks/use-toast';
import { Loader } from '@/components/ui/Loader';

export const InventoryTable = () => {
  const [artworks, setArtworks] = useState<Artwork[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingArtwork, setEditingArtwork] = useState<Artwork | null>(null);
  const [restockingArtwork, setRestockingArtwork] = useState<Artwork | null>(null);
  const [restockQuantity, setRestockQuantity] = useState(1);
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    price: 0,
    currency: 'INR',
    quantity: 1,
    status: 'draft'
  });
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

  const getCurrencySymbol = (currency: string) => {
    const symbols: { [key: string]: string } = {
      'INR': '₹',
      'USD': '$', 
      'EUR': '€',
      'GBP': '£'
    };
    return symbols[currency] || currency;
  };

  const handleEdit = (artwork: Artwork) => {
    setEditingArtwork(artwork);
    setEditForm({
      title: artwork.title,
      description: artwork.description || '',
      price: artwork.price,
      currency: artwork.currency,
      quantity: artwork.quantity,
      status: artwork.status
    });
  };

  const handleUpdateArtwork = async () => {
    if (!editingArtwork) return;
    
    try {
      await artworkService.updateArtwork(editingArtwork._id, editForm);
      
      // Update local state
      setArtworks(artworks.map(artwork => 
        artwork._id === editingArtwork._id 
          ? { ...artwork, ...editForm, status: editForm.status as 'draft' | 'published' | 'removed' | 'out_of_stock' }
          : artwork
      ));
      
      setEditingArtwork(null);
      toast({
        title: 'Success',
        description: 'Artwork updated successfully.',
      });
    } catch (error) {
      console.error('Error updating artwork:', error);
      toast({
        variant: 'destructive',
        title: 'Error', 
        description: 'Failed to update artwork.',
      });
    }
  };

  const handleRestock = async () => {
    if (!restockingArtwork || restockQuantity <= 0) return;
    
    try {
      const response = await artworkService.restockArtwork(restockingArtwork._id, restockQuantity);
      
      if (response.success && response.artwork) {
        // Update local state
        setArtworks(artworks.map(artwork => 
          artwork._id === restockingArtwork._id 
            ? response.artwork!
            : artwork
        ));
        
        setRestockingArtwork(null);
        setRestockQuantity(1);
        toast({
          title: 'Success',
          description: 'Artwork restocked successfully.',
        });
      }
    } catch (error) {
      console.error('Error restocking artwork:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to restock artwork.',
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
              <TableCell>{getCurrencySymbol(artwork.currency)}{artwork.price}</TableCell>
              <TableCell>{artwork.quantity}</TableCell>
              <TableCell>
                <Badge variant={
                  artwork.status === 'published' ? 'default' : 
                  artwork.status === 'out_of_stock' ? 'destructive' : 
                  'secondary'
                }>
                  {artwork.status.replace('_', ' ')}
                </Badge>
              </TableCell>
              <TableCell>{artwork.likeCount}</TableCell>
              <TableCell>
                <div className="flex gap-2">
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        disabled={artwork.status === 'published'}
                        onClick={() => handleEdit(artwork)}
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-md">
                      <DialogHeader>
                        <DialogTitle>Edit Artwork</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div>
                          <Label htmlFor="title">Title</Label>
                          <Input
                            id="title"
                            value={editForm.title}
                            onChange={(e) => setEditForm({...editForm, title: e.target.value})}
                          />
                        </div>
                        <div>
                          <Label htmlFor="description">Description</Label>
                          <Textarea
                            id="description"
                            value={editForm.description}
                            onChange={(e) => setEditForm({...editForm, description: e.target.value})}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="price">Price</Label>
                            <Input
                              id="price"
                              type="number"
                              value={editForm.price}
                              onChange={(e) => setEditForm({...editForm, price: parseFloat(e.target.value)})}
                            />
                          </div>
                          <div>
                            <Label htmlFor="currency">Currency</Label>
                            <Select 
                              value={editForm.currency} 
                              onValueChange={(value) => setEditForm({...editForm, currency: value})}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="INR">₹ INR</SelectItem>
                                <SelectItem value="USD">$ USD</SelectItem>
                                <SelectItem value="EUR">€ EUR</SelectItem>
                                <SelectItem value="GBP">£ GBP</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="quantity">Quantity</Label>
                            <Input
                              id="quantity"
                              type="number"
                              value={editForm.quantity}
                              onChange={(e) => setEditForm({...editForm, quantity: parseInt(e.target.value)})}
                            />
                          </div>
                          <div>
                            <Label htmlFor="status">Status</Label>
                            <Select 
                              value={editForm.status} 
                              onValueChange={(value) => setEditForm({...editForm, status: value})}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="draft">Draft</SelectItem>
                                <SelectItem value="published">Published</SelectItem>
                                <SelectItem value="out_of_stock">Out of Stock</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        <div className="flex gap-2 pt-4">
                          <Button onClick={handleUpdateArtwork} className="flex-1">
                            Update Artwork
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                  
                  {artwork.status === 'out_of_stock' && (
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => setRestockingArtwork(artwork)}
                        >
                          <Package className="w-4 h-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-md">
                        <DialogHeader>
                          <DialogTitle>Restock Artwork</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4">
                          <p className="text-sm text-muted-foreground">
                            Current quantity: {artwork.quantity}
                          </p>
                          <div>
                            <Label htmlFor="restock-quantity">Add Quantity</Label>
                            <Input
                              id="restock-quantity"
                              type="number"
                              min="1"
                              value={restockQuantity}
                              onChange={(e) => setRestockQuantity(parseInt(e.target.value))}
                            />
                          </div>
                          <div className="flex gap-2 pt-4">
                            <Button onClick={handleRestock} className="flex-1">
                              Restock
                            </Button>
                          </div>
                        </div>
                      </DialogContent>
                    </Dialog>
                  )}
                  
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