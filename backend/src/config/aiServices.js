// backend/src/config/aiServices.js

// FIXED: Updated to use correct environment variable names for Cloud Run deployment
module.exports = {
  // Vision AI / GenAI Service (deployed on Cloud Run in Part 2)
  visionAI: {
    // Primary: GENAI_SERVICE_URL from Cloud Run deployment
    // Fallback: AI_SERVICES_URL for local development
    baseURL: process.env.GENAI_SERVICE_URL || process.env.AI_SERVICES_URL || "http://localhost:5001",
    apiKey: process.env.AI_SERVICE_KEY || "",
  },
  
  // Gift AI Service (if you have one deployed)
  giftAI: {
    baseURL: process.env.GIFT_AI_SERVICE_URL || "http://localhost:8001",
    apiKey: process.env.AI_SERVICE_KEY || "",
  },
  
  // NOTE: Search AI is integrated directly with the frontend
  // No backend integration needed
};