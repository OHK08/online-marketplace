import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Heart, Share, ShoppingCart } from 'lucide-react';
import { useCopyLink } from '@/hooks/useCopyLink';

interface ItemCardProps {
  item: {
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
  };
  onLike: (id: string) => void;
  onWishlist: (id: string) => void;
  variant?: 'grid' | 'list';
}

export const ItemCard: React.FC<ItemCardProps> = ({ item, onLike, onWishlist, variant = 'grid' }) => {
  const { copyLink } = useCopyLink();

  const handleShare = () => {
    copyLink(`${window.location.origin}/item/${item.id}`, item.title);
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
    <Card className="card-hover overflow-hidden cursor-pointer" onClick={() => window.location.href = `/artwork/${item.id}`}>
      <div className="relative">
        <img src={item.image} alt={item.title} className="w-full h-48 object-cover" />
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-2 right-2 bg-background/80 hover:bg-background"
          onClick={() => onWishlist(item.id)}
        >
          <Heart className={`w-4 h-4 ${item.isWishlisted ? 'fill-red-500 text-red-500' : ''}`} />
        </Button>
      </div>
      <CardContent className="p-4">
        <h3 className="font-semibold mb-2">{item.title}</h3>
        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{item.description}</p>
        <div className="flex justify-between items-center mb-3">
          <span className="text-lg font-bold">{getCurrencySymbol(item.currency)}{item.price}</span>
          <div className="flex items-center gap-2">
            <Avatar className="w-6 h-6">
              <AvatarImage src={item.seller.avatar} />
              <AvatarFallback>{item.seller.name[0]}</AvatarFallback>
            </Avatar>
            <span className="text-sm text-muted-foreground">{item.seller.name}</span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onLike(item.id)}
            className={item.isLiked ? 'text-red-500' : ''}
          >
            <Heart className={`w-4 h-4 mr-1 ${item.isLiked ? 'fill-current' : ''}`} />
            {item.likes}
          </Button>
          <Button variant="ghost" size="sm" onClick={handleShare}>
            <Share className="w-4 h-4" />
          </Button>
          <Button size="sm" className="ml-auto btn-gradient">
            <ShoppingCart className="w-4 h-4 mr-1" />
            Add to Cart
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};