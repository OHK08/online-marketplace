import { useState, useEffect } from 'react';
import { StoryBar } from '@/components/ui/StoryBar';
import { ItemCard } from '@/components/ui/ItemCard';
import { Loader } from '@/components/ui/Loader';
import { artworkService, type Artwork } from '@/services/artwork';
import { useToast } from '@/hooks/use-toast';

interface ItemCardData {
  id: string;
  title: string;
  description: string;
  price: number;
  currency: string;
  image: string;
  seller: { id: string; name: string; avatar: string; };
  likes: number;
  isLiked: boolean;
  isWishlisted: boolean;
}

const DashboardPage = () => {
  const [items, setItems] = useState<ItemCardData[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    const loadArtworks = async () => {
      try {
        const response = await artworkService.getAllArtworks();
        if (response.success && response.artworks) {
          // Transform artwork data to match ItemCard interface
          const transformedItems: ItemCardData[] = response.artworks.map((artwork: Artwork) => ({
            id: artwork._id,
            title: artwork.title,
            description: artwork.description || '',
            price: artwork.price,
            currency: artwork.currency,
            image: artwork.media[0]?.url || '/placeholder.svg',
            seller: {
              id: artwork.artistId._id,
              name: artwork.artistId.name,
              avatar: artwork.artistId.avatarUrl || '/placeholder.svg',
            },
            likes: artwork.likeCount,
            isLiked: false,
            isWishlisted: false,
          }));
          setItems(transformedItems);
        }
      } catch (error) {
        console.error('Error loading artworks:', error);
        toast({
          variant: 'destructive',
          title: 'Error',
          description: 'Failed to load artworks. Please try again.',
        });
      } finally {
        setLoading(false);
      }
    };

    loadArtworks();
  }, [toast]);

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