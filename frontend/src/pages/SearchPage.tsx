// frontend/src/pages/SearchPage.tsx

import { useState, useEffect } from "react";
import {
  searchArtworks,
  getRecommendationsByUser,
  type Artwork,
} from "../services/searchAi";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [artworks, setArtworks] = useState<Artwork[]>([]);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<"recommendations" | "search">("recommendations");
  const { user } = useAuth();

  // Load initial recommendations on mount
  useEffect(() => {
    if (user) {
      loadRecommendations();
    }
  }, [user]);

  const loadRecommendations = async () => {
    if (!user?._id) {
      toast.error("Please log in to see recommendations");
      return;
    }

    setLoading(true);
    setMode("recommendations");
    
    try {
      const recommendations = await getRecommendationsByUser(user._id, 20);
      
      if (recommendations.length === 0) {
        // If no recommendations, show a helpful message but don't error
        toast.info("No recommendations yet. Try searching or liking some artworks!");
      }
      
      setArtworks(recommendations);
    } catch (error) {
      console.error('Error loading recommendations:', error);
      // Don't show error toast since we have fallback
      setArtworks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) {
      loadRecommendations();
      return;
    }

    setLoading(true);
    setMode("search");

    try {
      const results = await searchArtworks(query, {
        status: "published",
      });
      
      if (results.length === 0) {
        toast.info(`No results found for "${query}". Try a different search term.`);
      }
      
      setArtworks(results);
    } catch (error) {
      console.error('Error searching artworks:', error);
      toast.error('Search failed. Please try again.');
      setArtworks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const handleClearSearch = () => {
    setQuery("");
    loadRecommendations();
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Discover Artworks
          </h1>
          <p className="text-gray-600">
            {mode === "recommendations"
              ? "Curated products you'll adore... Personalized recommendations based on your likes"
              : `Search results for "${query}"`}
          </p>
        </div>

        {/* Search Bar */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-8">
          <div className="flex gap-3">
            <div className="flex-grow relative">
              <input
                type="text"
                placeholder="Search for artworks (e.g., vase, ganesh idol, handmade saree)..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              {query && (
                <button
                  onClick={handleClearSearch}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  aria-label="Clear search"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            <button
              onClick={handleSearch}
              disabled={loading}
              className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>

          {mode === "search" && (
            <button
              onClick={handleClearSearch}
              className="mt-3 text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              ← Back to recommendations
            </button>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Results Grid */}
        {!loading && artworks.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {artworks.map((artwork) => (
              <ArtworkCard key={artwork._id} artwork={artwork} />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && artworks.length === 0 && (
          <div className="text-center py-20">
            <div className="text-gray-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">
              {mode === "recommendations" 
                ? "Start Exploring!" 
                : "No results found"}
            </h3>
            <p className="text-gray-500 mb-6">
              {mode === "recommendations"
                ? "Try searching for artworks like 'vase', 'ganesh idol', or 'handmade crafts'"
                : `No artworks found for "${query}". Try different keywords.`}
            </p>
            {mode === "search" && (
              <button
                onClick={handleClearSearch}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Clear search and explore
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Artwork Card Component
function ArtworkCard({ artwork }: { artwork: Artwork }) {
  const imageUrl = artwork.media?.[0]?.url || "/placeholder-artwork.jpg";
  const price = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: artwork.currency || "INR",
  }).format(artwork.price);

  const handleViewArtwork = () => {
    window.location.href = `/artwork/${artwork._id}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-lg transition-shadow group">
      {/* Image - Clickable */}
      <div 
        className="relative aspect-square overflow-hidden bg-gray-100 cursor-pointer"
        onClick={handleViewArtwork}
      >
        <img
          src={imageUrl}
          alt={artwork.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
        />
        {artwork.tags && artwork.tags.length > 0 && (
          <div className="absolute top-2 left-2 flex flex-wrap gap-1">
            {artwork.tags.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="bg-white/90 backdrop-blur-sm text-xs px-2 py-1 rounded-full text-gray-700 font-medium"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 
          className="font-semibold text-gray-900 mb-1 line-clamp-1 cursor-pointer hover:text-blue-600 transition-colors"
          onClick={handleViewArtwork}
        >
          {artwork.title}
        </h3>
        <p className="text-sm text-gray-600 mb-2">by {artwork.artistName}</p>
        
        {artwork.description && (
          <p className="text-sm text-gray-500 mb-3 line-clamp-2">
            {artwork.description}
          </p>
        )}

        <div className="flex items-center justify-between">
          <span className="text-lg font-bold text-gray-900">{price}</span>
          <button 
            onClick={handleViewArtwork}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            View
          </button>
        </div>
      </div>
    </div>
  );
}