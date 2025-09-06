import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Heart, Share, ShoppingCart, ArrowLeft } from 'lucide-react';
import { artworkService } from '@/services/artwork';
import { Loader } from '@/components/ui/Loader';
import { useToast } from '@/hooks/use-toast';
import { useCopyLink } from '@/hooks/useCopyLink';

export const ArtworkDetailPage = () => {
  const { id } = useParams();
  const [artwork, setArtwork] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isLiked, setIsLiked] = useState(false);
  const [isWishlisted, setIsWishlisted] = useState(false);
  const { toast } = useToast();
  const { copyLink } = useCopyLink();

  useEffect(() => {
    if (id) {
      fetchArtwork();
    }
  }, [id]);

  const fetchArtwork = async () => {
    try {
      const response = await artworkService.getArtworkById(id!);
      if (response.success && response.artwork) {
        setArtwork(response.artwork);
      }
    } catch (error) {
      console.error('Error fetching artwork:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load artwork details',
      });
    } finally {
      setLoading(false);
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

  const handleShare = () => {
    copyLink(window.location.href, artwork?.title);
  };

  const handleLike = () => {
    setIsLiked(!isLiked);
    toast({
      description: isLiked ? 'Removed from likes' : 'Added to likes',
    });
  };

  const handleWishlist = () => {
    setIsWishlisted(!isWishlisted);
    toast({
      description: isWishlisted ? 'Removed from wishlist' : 'Added to wishlist',
    });
  };

  if (loading) {
    return <Loader text="Loading artwork details..." />;
  }

  if (!artwork) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Artwork not found</h1>
          <p className="text-muted-foreground mb-4">The artwork you're looking for doesn't exist.</p>
          <Button onClick={() => window.history.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <Button 
          variant="ghost" 
          onClick={() => window.history.back()}
          className="mb-6"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Image Gallery */}
          <div className="space-y-4">
            <div className="aspect-square rounded-lg overflow-hidden bg-muted">
              <img
                src={artwork.media[currentImageIndex]?.url || '/placeholder.svg'}
                alt={artwork.title}
                className="w-full h-full object-cover"
              />
            </div>
            {artwork.media.length > 1 && (
              <div className="flex gap-2 overflow-x-auto">
                {artwork.media.map((media: any, index: number) => (
                  <button
                    key={index}
                    onClick={() => setCurrentImageIndex(index)}
                    className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 ${
                      currentImageIndex === index ? 'border-primary' : 'border-transparent'
                    }`}
                  >
                    <img
                      src={media.url}
                      alt={`${artwork.title} ${index + 1}`}
                      className="w-full h-full object-cover"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Product Details */}
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold mb-2">{artwork.title}</h1>
              <p className="text-2xl font-bold text-primary">
                {getCurrencySymbol(artwork.currency)}{artwork.price}
              </p>
            </div>

            <div className="flex items-center gap-4">
              <Avatar className="w-12 h-12">
                <AvatarImage src={artwork.artistId.avatarUrl} />
                <AvatarFallback>{artwork.artistId.name[0]}</AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-semibold">{artwork.artistId.name}</h3>
                <p className="text-sm text-muted-foreground">Artist</p>
              </div>
            </div>

            <div className="flex gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={handleLike}
                className={isLiked ? 'text-red-500 border-red-500' : ''}
              >
                <Heart className={`w-4 h-4 mr-2 ${isLiked ? 'fill-current' : ''}`} />
                {isLiked ? 'Liked' : 'Like'}
              </Button>
              <Button variant="outline" size="sm" onClick={handleShare}>
                <Share className="w-4 h-4 mr-2" />
                Share
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleWishlist}
                className={isWishlisted ? 'text-primary border-primary' : ''}
              >
                <Heart className={`w-4 h-4 mr-2 ${isWishlisted ? 'fill-current' : ''}`} />
                {isWishlisted ? 'Wishlisted' : 'Wishlist'}
              </Button>
            </div>

            <Card>
              <CardContent className="p-6">
                <h3 className="font-semibold mb-3">Product Details</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Quantity Available:</span>
                    <span className="font-medium">{artwork.quantity}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status:</span>
                    <Badge variant="secondary">{artwork.status}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Currency:</span>
                    <span className="font-medium">{artwork.currency}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {artwork.description && (
              <Card>
                <CardContent className="p-6">
                  <h3 className="font-semibold mb-3">Description</h3>
                  <p className="text-muted-foreground leading-relaxed whitespace-pre-wrap">
                    {artwork.description}
                  </p>
                </CardContent>
              </Card>
            )}

            <Button size="lg" className="w-full btn-gradient">
              <ShoppingCart className="w-5 h-5 mr-2" />
              Add to Cart
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};