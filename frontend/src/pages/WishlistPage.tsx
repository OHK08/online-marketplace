import { useState } from 'react';
import { ItemCard } from '@/components/ui/ItemCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Heart, Search, Grid, List } from 'lucide-react';

// Mock wishlist data
const mockWishlistItems = [
  {
    id: '2',
    title: 'Vintage Leather Journal',
    description: 'Premium leather-bound journal with handmade paper pages.',
    price: 45.00,
    currency: 'USD',
    image: 'https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=400',
    seller: {
      id: '2',
      name: 'Michael Chen',
      avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100',
    },
    likes: 18,
    isLiked: true,
    isWishlisted: true,
  },
  {
    id: '6',
    title: 'Organic Skincare Set',
    description: 'Natural skincare products made with organic ingredients.',
    price: 92.00,
    currency: 'USD',
    image: 'https://images.unsplash.com/photo-1556228578-8c89e6adf883?w=400',
    seller: {
      id: '6',
      name: 'Natural Beauty',
      avatar: 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=100',
    },
    likes: 28,
    isLiked: true,
    isWishlisted: true,
  },
];

const WishlistPage = () => {
  const [wishlistItems, setWishlistItems] = useState(mockWishlistItems);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  const handleLike = (itemId: string) => {
    setWishlistItems(prevItems =>
      prevItems.map(item =>
        item.id === itemId
          ? {
              ...item,
              isLiked: !item.isLiked,
              likes: item.isLiked ? item.likes - 1 : item.likes + 1,
            }
          : item
      )
    );
  };

  const handleWishlist = (itemId: string) => {
    setWishlistItems(prevItems =>
      prevItems.filter(item => item.id !== itemId)
    );
  };

  const filteredItems = wishlistItems.filter(item =>
    item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.seller.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (wishlistItems.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <EmptyState
            icon={Heart}
            title="Your Wishlist is Empty"
            description="Start browsing and save items you love to see them here"
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
          <h1 className="text-3xl font-bold mb-2">My Wishlist</h1>
          <p className="text-muted-foreground">
            {wishlistItems.length} {wishlistItems.length === 1 ? 'item' : 'items'} saved for later
          </p>
        </div>

        {/* Search and Controls */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input
              placeholder="Search wishlist..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <div className="flex gap-2">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('grid')}
              className="flex items-center gap-2"
            >
              <Grid className="w-4 h-4" />
              Grid
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setViewMode('list')}
              className="flex items-center gap-2"
            >
              <List className="w-4 h-4" />
              List
            </Button>
          </div>
        </div>

        {/* Wishlist Items */}
        {filteredItems.length > 0 ? (
          <div className={viewMode === 'grid' ? 'masonry-grid' : 'space-y-4'}>
            {filteredItems.map((item) => (
              <div key={item.id} className={viewMode === 'grid' ? 'masonry-item' : ''}>
                <ItemCard
                  item={item}
                  onLike={handleLike}
                  onWishlist={handleWishlist}
                  variant={viewMode}
                />
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Search}
            title="No Items Found"
            description="Try adjusting your search criteria"
          />
        )}
      </div>
    </div>
  );
};

export default WishlistPage;