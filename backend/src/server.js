// ------------------- Imports -------------------
const express = require("express");
const dotenv = require("dotenv");
const cookieParser = require("cookie-parser");
const cors = require("cors");
const multer = require("multer");

// ------------------- Configs -------------------
const database = require("./config/database");
const { cloudinaryConnect } = require("./config/cloudinary");

// ------------------- Routes -------------------
const authRoutes = require("./routes/authRoutes");
const userRoutes = require("./routes/userRoutes");
const artworkRoutes = require("./routes/artworkRoutes");
const orderRoutes = require("./routes/orderRoutes");
const likeRoutes = require("./routes/likeRoutes");
const cartRoutes = require("./routes/cartRoutes");
const visionRoutes = require("./routes/visionRoutes");
const searchRoutes = require("./routes/searchRoutes");
const recommendationRoutes = require("./routes/recommendationRoutes");
const giftAIRoutes = require("./routes/giftAIRoutes");

// ------------------- Initialize -------------------
dotenv.config();
const app = express();
const PORT = process.env.PORT || 4000;

// ------------------- Database & Cloudinary -------------------
database.connect();
cloudinaryConnect();

// ------------------- Middlewares -------------------
// Parse JSON and cookies
app.use(express.json());
app.use(cookieParser());

// Allowed frontend origins
const allowedOrigins = [
  process.env.FRONTEND_URL, // from env variable
  "http://localhost:5173", // local dev
].filter(Boolean); // Remove undefined values

// CORS setup
const corsOptions = {
  origin: function (origin, callback) {
    // Allow requests with no origin (mobile apps, curl, Postman, etc.)
    if (!origin) return callback(null, true);
    
    if (!allowedOrigins.includes(origin)) {
      console.warn(`🚫 CORS blocked request from origin: ${origin}`);
      return callback(new Error("CORS not allowed for this origin"), false);
    }
    return callback(null, true);
  },
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
  allowedHeaders: ["Content-Type", "Authorization"],
};

// Apply CORS to all routes
app.use(cors(corsOptions));

// Handle all OPTIONS (preflight) requests globally
app.options("*", cors(corsOptions));

// ------------------- Routes -------------------
app.use("/api/v1/auth", authRoutes);
app.use("/api/v1/user", userRoutes);
app.use("/api/v1/artworks", artworkRoutes);
app.use("/api/v1/order", orderRoutes);
app.use("/api/v1/like", likeRoutes);
app.use("/api/v1/cart", cartRoutes);
app.use("/api/v1/vision", visionRoutes);
app.use("/api/v1/search-ai/search", searchRoutes);
app.use("/api/v1/search-ai/recommendations", recommendationRoutes);
app.use("/api/v1/gift-ai", giftAIRoutes);

// ------------------- Health Check -------------------
app.get("/", (req, res) => {
  return res.json({
    success: true,
    message: "✅ Orchid backend is running successfully!",
    service: "Backend API",
    frontend: process.env.FRONTEND_URL,
  });
});

// ------------------- Error Handling Middleware -------------------
app.use((err, req, res, next) => {
  console.error("=== GLOBAL ERROR HANDLER ===");
  console.error("🔥 Server Error:", err);
  
  // Handle multer errors
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        success: false,
        message: 'File size too large. Maximum size is 10MB',
      });
    }
    return res.status(400).json({
      success: false,
      message: `File upload error: ${err.message}`,
    });
  }
  
  // Handle invalid file type errors
  if (err.message && err.message.includes('Invalid file type')) {
    return res.status(400).json({
      success: false,
      message: err.message,
    });
  }
  
  // Handle CORS errors
  if (err.message && err.message.includes('CORS')) {
    return res.status(403).json({
      success: false,
      message: 'CORS error: Origin not allowed',
    });
  }
  
  // Generic error handler
  res.status(500).json({
    success: false,
    message: 'Internal Server Error',
    error: err.message,
    stack: process.env.NODE_ENV === 'development' ? err.stack : undefined,
  });
});

// ------------------- Start Server -------------------
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📦 Backend API: http://localhost:${PORT}`);
  console.log(`🎁 Gift AI Service: ${process.env.GIFT_AI_SERVICE_URL || "http://localhost:8001"}`);
  console.log(`👁️  Vision AI Service: ${process.env.VISION_AI_SERVICE_URL || "http://localhost:8004"}`);
  console.log(`🌐 Allowed Origins: ${allowedOrigins.join(", ")}`);
});