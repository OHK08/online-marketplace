// backend/src/routes/recommendationRoutes.js
const express = require("express");
const ctrl = require("../controllers/searchController");

const router = express.Router();

// --- Recommendation Routes ---
router.post("/similar", ctrl.recommendationsSimilar);  // POST /api/search-ai/recommendations/similar
router.get("/health", ctrl.recommendationsHealth);     // GET  /api/search-ai/recommendations/health
router.get("/analytics", ctrl.recommendationsAnalytics); // GET  /api/search-ai/recommendations/analytics

module.exports = router;
