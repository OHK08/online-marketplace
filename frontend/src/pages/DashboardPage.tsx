import { useState, useEffect } from 'react';
import { StoryBar } from '@/components/ui/StoryBar';
import { ItemCard } from '@/components/ui/ItemCard';
import { Loader } from '@/components/ui/Loader';

// Mock data for the feed
const mockItems = [
  {
    id: '1',
    title: 'Handcrafted Ceramic Vase',
    description: 'Beautiful handmade ceramic vase perfect for your home decor.',
    price: 89.99,
    image: 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400',
    seller: {
      id: '1',
      name: 'Sarah Johnson',
      avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b714?w=100',
    },
    likes: 24,
    isLiked: false,
    isWishlisted: false,
  },
  {
    id: '2',
    title: 'Vintage Leather Journal',
    description: 'Premium leather-bound journal with handmade paper pages.',
    price: 45.00,
    image: 'https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=400',
    seller: {
      id: '2',
      name: 'Michael Chen',
      avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100',
    },
    likes: 18,
    isLiked: true,
    isWishlisted: false,
  },
  {
    id: '3',
    title: 'Artisan Coffee Beans',
    description: 'Single-origin coffee beans roasted to perfection.',
    price: 24.99,
    image: 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400',
    seller: {
      id: '3',
      name: 'Coffee Roasters Co.',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100',
    },
    likes: 42,
    isLiked: false,
    isWishlisted: true,
  },
  {
    id: '4',
    title: 'Minimalist Wall Art',
    description: 'Modern geometric print perfect for contemporary spaces.',
    price: 35.00,
    image: 'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=400',
    seller: {
      id: '4',
      name: 'Art Studio',
      avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100',
    },
    likes: 31,
    isLiked: false,
    isWishlisted: false,
  },
  {
    id: '5',
    title: 'Handwoven Scarf',
    description: 'Soft alpaca wool scarf with traditional patterns.',
    price: 68.00,
    image: 'https://images.unsplash.com/photo-1601924994987-69e26d50dc26?w=400',
    seller: {
      id: '5',
      name: 'Textile Artisan',
      avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100',
    },
    likes: 15,
    isLiked: false,
    isWishlisted: false,
  },
  {
    id: '6',
    title: 'Organic Skincare Set',
    description: 'Natural skincare products made with organic ingredients.',
    price: 92.00,
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

const DashboardPage = () => {
  const [items, setItems] = useState<typeof mockItems>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate API call
    const loadItems = async () => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setItems(mockItems);
      setLoading(false);
    };

    loadItems();
  }, []);

  const handleLike = (itemId: string) => {
    setItems(prevItems =>
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
    setItems(prevItems =>
      prevItems.map(item =>
        item.id === itemId
          ? { ...item, isWishlisted: !item.isWishlisted }
          : item
      )
    );
  };

  if (loading) {
    return <Loader text="Loading your feed..." />;
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Stories Bar */}
        <div className="mb-8">
          <StoryBar />
        </div>

        {/* Feed Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-2">Discover Amazing Products</h1>
          <p className="text-muted-foreground">
            Curated just for you from our community of creative sellers
          </p>
        </div>

        {/* Masonry Grid */}
        <div className="masonry-grid">
          {items.map((item) => (
            <div key={item.id} className="masonry-item">
              <ItemCard
                item={item}
                onLike={handleLike}
                onWishlist={handleWishlist}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;