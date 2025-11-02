import axios from 'axios';

// Separate axios instance for veo-api-service
const veoApiClient = axios.create({
  baseURL: 'https://veo-api-service-529829749133.asia-south1.run.app',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Reel interface based on the artwork document structure
export interface Reel {
  _id: string;
  title: string;
  artistName: string;
  generatedVideoUrl: string; // This will be the signed URL from the backend
  description?: string;
  createdAt?: string;
}

export interface ReelsResponse {
  success: boolean;
  message?: string;
  reels?: Reel[];
  count?: number;
}

export const reelsService = {
  /**
   * Fetch all video reels from the veo-api-service
   * @returns Promise<ReelsResponse>
   */
  async fetchReelsFeed(): Promise<ReelsResponse> {
    const response = await veoApiClient.get('/reels');
    
    // The API returns a plain array, so we wrap it in our expected format
    if (Array.isArray(response.data)) {
      return {
        success: true,
        reels: response.data,
        count: response.data.length
      };
    }
    
    // If it's already in the expected format, return as is
    return response.data;
  },
};