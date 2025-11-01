// backend/src/controllers/searchController.js
const searchAI = require("../services/searchAI");

exports.search = async (req, res) => {
  try {
    const result = await searchAI.search(req.body);
    res.json(result.data);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
};

exports.searchStats = async (req, res) => {
  try {
    const result = await searchAI.searchStats();
    res.json(result.data);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
};

exports.searchHealth = async (req, res) => {
  try {
    const result = await searchAI.searchHealth();
    res.json(result.data);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
};

exports.searchIndex = async (req, res) => {
  try {
    const { id, text, payload } = req.body;

    if (!id || !text || !payload) {
      return res.status(400).json({
        error: "Invalid request. id, text, and payload are required.",
      });
    }

    const result = await searchAI.searchIndex({ id, text, payload });
    return res.json(result.data);
  } catch (err) {
    console.error("searchIndex error:", err.response?.data || err.message || err.toString());
    return res.status(502).json({
      error: "SearchAI service error",
      details: err.message || "Unknown error",
    });
  }
};


// Cultural search
exports.searchCultural = async (req, res) => {
  try {
    const result = await searchAI.searchCultural(req.body);
    res.json(result.data);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
};

exports.searchCulturalCategories = async (req, res) => {
  try {
    const result = await searchAI.searchCulturalCategories();
    res.json(result.data);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
};

exports.searchCulturalSeasonal = async (req, res) => {
  try {
    const result = await searchAI.searchCulturalSeasonal();
    res.json(result.data);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
};

// Recommendations
exports.recommendationsSimilar = async (req, res) => {
  try {
    const result = await searchAI.recommendationsSimilar(req.body);
    res.json(result.data);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
};

exports.recommendationsHealth = async (req, res) => {
  try {
    const result = await searchAI.recommendationsHealth();
    res.json(result.data);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
};

exports.recommendationsAnalytics = async (req, res) => {
  try {
    const result = await searchAI.recommendationsAnalytics();
    res.json(result.data);
  } catch (err) {
    res.status(502).json({ error: err.message });
  }
};
