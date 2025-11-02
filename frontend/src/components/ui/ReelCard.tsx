import { useRef, useState, useEffect } from 'react';
import { Reel } from '@/services/reels';
import { Heart, Search, Play, Volume2, VolumeX } from 'lucide-react';

interface ReelCardProps {
  reel: Reel;
}

const ReelCard = ({ reel }: ReelCardProps) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const [isMuted, setIsMuted] = useState(true);

  // ✅ Autoplay / pause based on visibility
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (videoRef.current) {
          if (entry.isIntersecting) {
            videoRef.current.play().catch(err => console.log('Autoplay prevented:', err));
          } else {
            videoRef.current.pause();
          }
        }
      },
      { threshold: 0.5 }
    );

    if (videoRef.current) observer.observe(videoRef.current);

    return () => observer.disconnect();
  }, []);

  // ✅ Toggle mute/unmute
  const toggleMute = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (videoRef.current) {
      videoRef.current.muted = !videoRef.current.muted;
      setIsMuted(videoRef.current.muted);
    }
  };

  // ✅ Optional manual click play/pause (still supported)
  const handleVideoClick = () => {
    if (videoRef.current) {
      if (videoRef.current.paused) videoRef.current.play();
      else videoRef.current.pause();
    }
  };

  return (
    <div
      className="relative break-inside-avoid rounded-lg overflow-hidden bg-gray-900 group cursor-pointer"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* 🎬 Autoplay Video */}
      <video
        ref={videoRef}
        src={reel.generatedVideoUrl}
        className="w-full h-auto object-cover"
        loop
        muted={isMuted}
        playsInline
        autoPlay
        preload="auto"
        onClick={handleVideoClick}
        onLoadedData={() => {
          if (videoRef.current) {
            videoRef.current.play().catch(err => console.log('Autoplay prevented:', err));
          }
        }}
        poster={reel.generatedVideoUrl.replace('.mp4', '_thumbnail.jpg')}
      />

      {/* ▶ Hover Overlay */}
      <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
        <div className="bg-white/90 rounded-full p-4">
          <Play className="w-8 h-8 text-black fill-black" />
        </div>
      </div>

      {/* 🖤 Bottom Gradient Info */}
      <div
        className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent p-4 transition-opacity duration-300 ${
          isHovered ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <div className="flex items-end justify-between">
          {/* Left Side: Info */}
          <div className="flex-1 pr-2">
            <h3 className="text-white text-sm font-semibold line-clamp-2 mb-1">
              {reel.title}
            </h3>
            <p className="text-white/70 text-xs">{reel.artistName}</p>
          </div>

          {/* Right Side: Buttons */}
          <div className="flex flex-col gap-2">
            <button
              className="bg-white/20 backdrop-blur-sm rounded-full p-2 hover:bg-white/30 transition-colors"
              aria-label="Like"
              onClick={(e) => e.stopPropagation()}
            >
              <Heart className="w-4 h-4 text-white" />
            </button>

            <button
              className="bg-white/20 backdrop-blur-sm rounded-full p-2 hover:bg-white/30 transition-colors"
              aria-label="View Details"
              onClick={(e) => e.stopPropagation()}
            >
              <Search className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>
      </div>

      {/* 🏷 Artist Badge */}
      <div
        className={`absolute top-3 left-3 bg-black/50 backdrop-blur-sm px-3 py-1.5 rounded-full transition-opacity duration-300 ${
          isHovered ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <span className="text-white text-xs font-medium">{reel.artistName}</span>
      </div>

      {/* 🔇 Mute / Unmute */}
      <button
        className={`absolute top-3 right-3 bg-black/50 backdrop-blur-sm rounded-full p-2 hover:bg-black/70 transition-all duration-300 ${
          isHovered ? 'opacity-100' : 'opacity-0'
        }`}
        onClick={toggleMute}
        aria-label={isMuted ? 'Unmute' : 'Mute'}
      >
        {isMuted ? (
          <VolumeX className="w-4 h-4 text-white" />
        ) : (
          <Volume2 className="w-4 h-4 text-white" />
        )}
      </button>
    </div>
  );
};

export default ReelCard;
