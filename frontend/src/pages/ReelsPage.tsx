import { useState, useEffect } from 'react';
import { reelsService, Reel } from '@/services/reels';
import { Loader } from '@/components/ui/Loader';
import { EmptyState } from '@/components/ui/EmptyState';
import ReelCard from '@/components/ui/ReelCard';
import { AlertCircle, Video } from 'lucide-react';

const ReelsPage = () => {
  const [reels, setReels] = useState<Reel[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadReels = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await reelsService.fetchReelsFeed();
        
        if (response.success && response.reels) {
          setReels(response.reels);
        } else {
          setError('Failed to load reels');
        }
      } catch (err) {
        console.error('Error fetching reels:', err);
        setError('Unable to load video reels. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    loadReels();
  }, []);

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <Loader size="lg" text="Loading reels..." />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <EmptyState
          icon={AlertCircle}
          title="Oops! Something went wrong"
          description={error}
        />
      </div>
    );
  }

  // Empty state
  if (reels.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <EmptyState
          icon={Video}
          title="No Reels Available"
          description="Check back later for amazing AI-generated video content!"
        />
      </div>
    );
  }

  // Main render: Sora-style masonry grid layout
  return (
    <div className="min-h-screen bg-black overflow-y-auto">
      <div className="container mx-auto px-4 py-6">
        {/* Masonry Grid Layout */}
        <div className="columns-1 sm:columns-2 lg:columns-3 xl:columns-4 gap-4 space-y-4">
          {reels.map((reel) => (
            <ReelCard key={reel._id} reel={reel} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default ReelsPage;