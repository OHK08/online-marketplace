// backend/src/services/searchAI.js
const axios = require("axios");
const { searchAI } = require("../config/aiServices");

/**
 * Create axios client with baseURL + API key
 */
function _client() {
  return axios.create({
    baseURL: searchAI.baseURL,
    timeout: 60000,
    headers: {
      "x-api-key": searchAI.apiKey,
      "Content-Type": "application/json",
    },
  });
}

// -----------------------------
// SEARCH ROUTES
// -----------------------------

/**
 * Basic semantic/vector search
 */
exports.search = (data) => _client().post("/search", data);

/**
 * Collection statistics
 */
exports.searchStats = () => _client().get("/search/stats");

/**
 * Health check
 */
exports.searchHealth = () => _client().get("/search/health");

/**
 * Index a new item (POST)
 */
exports.searchIndex = (data) => _client().post("/search/index", data);

// -----------------------------
// CULTURAL SEARCH ROUTES
// -----------------------------

/**
 * Cultural search (with filters, cultural context, etc.)
 */
exports.searchCultural = (data) => _client().post("/search/cultural", data);

/**
 * Get available cultural categories
 */
exports.searchCulturalCategories = () => _client().get("/search/cultural/categories");

/**
 * Get seasonal cultural items
 */
exports.searchCulturalSeasonal = () => _client().get("/search/cultural/seasonal");

// -----------------------------
// RECOMMENDATION ROUTES
// -----------------------------

/**
 * Get similar item recommendations
 */
exports.recommendationsSimilar = (data) => _client().post("/recommendations/similar", data);

/**
 * Recommendation service health
 */
exports.recommendationsHealth = () => _client().get("/recommendations/health");

/**
 * Recommendation analytics
 */
exports.recommendationsAnalytics = () => _client().get("/recommendations/analytics");