// backend/src/config/aiServices.js
module.exports = {
  visionAI: {
    baseURL: process.env.AI_SERVICES_URL || "http://localhost:5001",
    apiKey: process.env.AI_SERVICE_KEY || "",
  },
  searchAI: {
    baseURL: process.env.SEARCH_AI_URL || "http://localhost:8000",
    apiKey: process.env.AI_SERVICE_KEY || "",
  },
};
