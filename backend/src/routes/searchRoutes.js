// backend/src/routes/searchRoutes.js
const express = require("express");
const ctrl = require("../controllers/searchController");

const router = express.Router();

// --- Search Routes ---
router.post("/", ctrl.search); // POST /api/search-ai/search
router.get("/stats", ctrl.searchStats); // GET  /api/search-ai/search/stats
router.get("/health", ctrl.searchHealth); // GET  /api/search-ai/search/health
router.post("/index", ctrl.searchIndex); // GET  /api/search-ai/search/index

// --- Cultural Search ---
router.post("/cultural", ctrl.searchCultural); // POST /api/search-ai/search/cultural
router.get("/cultural/categories", ctrl.searchCulturalCategories); // GET  /api/search-ai/search/cultural/categories
router.get("/cultural/seasonal", ctrl.searchCulturalSeasonal); // GET  /api/search-ai/search/cultural/seasonal

module.exports = router;
