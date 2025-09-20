// backend/src/config/aiServices.js
module.exports = {
  visionAI: {
    baseURL: process.env.AI_SERVICES_URL || "https://online-marketplace-visionai.onrender.com/api/v1/",
    apiKey: process.env.AI_SERVICE_KEY || "srv-d36p196uk2gs73a6qmj0",
  },
  searchAI: {
    baseURL: process.env.SEARCH_AI_URL || "http://localhost:8000",
    apiKey: process.env.AI_SERVICE_KEY || "",
  },
};
