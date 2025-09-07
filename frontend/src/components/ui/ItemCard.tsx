import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Heart, Share, ShoppingCart } from 'lucide-react';
import { useCopyLink } from '@/hooks/useCopyLink';
import { likeService } from '@/services/like';
import { useState } from 'react';
import { toast } from 'sonner';
import type { Artwork } from '@/services/artwork';

interface ItemCardProps {
  item: Artwork;
  onLike?: (id: string) => void;
  onWishlist?: (id: string) => void;
  variant?: 'grid' | 'list';
  isLiked?: boolean;
}

export const ItemCard: React.FC<ItemCardProps> = ({
  item,
  onLike,
  onWishlist,
  variant = 'grid',
  isLiked = false
}) => {
  const { copyLink } = useCopyLink();
  const [liked, setLiked] = useState(isLiked);
  const [likeCount, setLikeCount] = useState(item.likeCount || 0);

  const handleShare = () => {
    copyLink(`${window.location.origin}/artwork/${item._id}`, item.title);
  };

  const handleLike = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await likeService.toggleLike(item._id);
      setLiked(!liked);
      setLikeCount(prev => liked ? prev - 1 : prev + 1);
      onLike?.(item._id);
    } catch (error) {
      toast.error('Failed to update like');
    }
  };

  const handleWishlist = (e: React.MouseEvent) => {
    e.stopPropagation();
    onWishlist?.(item._id);
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

  return (
    <Card className="card-hover overflow-hidden cursor-pointer" onClick={() => window.location.href = `/artwork/${item._id}`}>
      <div className="relative">
        <img src={item.media[0]?.url || '/placeholder.svg'} alt={item.title} className="w-full h-48 object-cover" />
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-2 right-2 bg-background/80 hover:bg-background"
          onClick={handleWishlist}
        >
          <Heart className={`w-4 h-4 ${liked ? 'fill-red-500 text-red-500' : ''}`} />
        </Button>
      </div>
      <CardContent className="p-4">
        <h3 className="font-semibold mb-2">{item.title}</h3>
        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{item.description}</p>
        <div className="flex justify-between items-center mb-3">
          <span className="text-lg font-bold">
            {item.currency ? getCurrencySymbol(item.currency) : ''}
            {item.price ?? 'N/A'}
          </span>
          <div className="flex items-center gap-2">
            <Avatar className="w-6 h-6">
              <AvatarImage src={item.artistId?.avatarUrl || '/placeholder.svg'} />
              <AvatarFallback>
                {item.artistId?.name ? item.artistId.name[0] : '?'}
              </AvatarFallback>
            </Avatar>
            <span className="text-sm text-muted-foreground">
              {item.artistId?.name || 'Unknown Artist'}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLike}
            className={liked ? 'text-red-500' : ''}
          >
            <Heart className={`w-4 h-4 mr-1 ${liked ? 'fill-current' : ''}`} />
            {likeCount}
          </Button>
          <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); handleShare(); }}>
            <Share className="w-4 h-4" />
          </Button>
          <Button size="sm" className="ml-auto btn-gradient" onClick={(e) => e.stopPropagation()}>
            <ShoppingCart className="w-4 h-4 mr-1" />
            Add to Cart
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};