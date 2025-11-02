// ------------------- Imports -------------------
const express = require("express");
const dotenv = require("dotenv");
const cookieParser = require("cookie-parser");
const cors = require("cors");
const multer = require("multer");

// ------------------- Configs -------------------
const database = require("./config/database");
const { cloudinaryConnect } = require("./config/cloudinary");

// ------------------- Initialize -------------------
dotenv.config();
const app = express();
const PORT = process.env.PORT || 8080; // Required for Cloud Run

// ------------------- Database & Cloudinary -------------------
database.connect();
cloudinaryConnect();

// ------------------- Middlewares -------------------
app.use(express.json());
app.use(cookieParser());

// Allowed frontend origins
// Support multiple frontend origins, from env or defaults
const allowedOrigins = (
  process.env.FRONTEND_URL ||
  process.env.FRONTEND_ORIGIN ||
  "http://localhost:5173,http://localhost:3000"
)
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

// CORS setup
const corsOptions = {
  origin: function (origin, callback) {
    if (!origin) return callback(null, true); // Allow non-browser clients
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

app.use(cors(corsOptions));
app.options("*", cors(corsOptions));

// ------------------- Safe Route Loader -------------------
function safeRouteLoad(path, routeName) {
  try {
    console.log(`🔗 Loading ${routeName}...`);
    const route = require(path);
    app.use(`/api/v1/${routeName}`, route);
    console.log(`✅ Loaded ${routeName}`);
  } catch (err) {
    console.error(`❌ Failed to load ${routeName}:`, err.message);
  }
}

// ------------------- Routes -------------------
safeRouteLoad("./routes/authRoutes", "auth");
safeRouteLoad("./routes/userRoutes", "user");
safeRouteLoad("./routes/artworkRoutes", "artworks");
safeRouteLoad("./routes/orderRoutes", "order");
safeRouteLoad("./routes/likeRoutes", "like");
safeRouteLoad("./routes/cartRoutes", "cart");
safeRouteLoad("./routes/visionRoutes", "vision");
safeRouteLoad("./routes/giftAIRoutes", "gift-ai");

// ------------------- Health Check -------------------
app.get("/", (req, res) => {
  res.json({
    success: true,
    message: "✅ Orchid backend is running successfully!",
    service: "Backend API",
    environment: process.env.NODE_ENV || "development",
    allowedOrigins,
  });
});

// ------------------- Error Handling Middleware -------------------
app.use((err, req, res, next) => {
  console.error("=== GLOBAL ERROR HANDLER ===");
  console.error("🔥 Server Error:", err);

  if (err instanceof multer.MulterError) {
    if (err.code === "LIMIT_FILE_SIZE") {
      return res.status(400).json({
        success: false,
        message: "File size too large. Maximum size is 10MB",
      });
    }
    return res.status(400).json({
      success: false,
      message: `File upload error: ${err.message}`,
    });
  }

  if (err.message && err.message.includes("Invalid file type")) {
    return res.status(400).json({ success: false, message: err.message });
  }

  if (err.message && err.message.includes("CORS")) {
    return res.status(403).json({
      success: false,
      message: "CORS error: Origin not allowed",
    });
  }

  res.status(500).json({
    success: false,
    message: "Internal Server Error",
    error: err.message,
    stack: process.env.NODE_ENV === "development" ? err.stack : undefined,
  });
});

// ------------------- Start Server -------------------
try {
  app.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`);
    console.log(`📦 Backend API: http://localhost:${PORT}`);
    console.log(`🎁 Gift AI Service: ${process.env.GIFT_AI_SERVICE_URL || "Not configured"}`);
    console.log(`👁️  Vision AI Service: ${process.env.GENAI_SERVICE_URL || "Not configured"}`);
    console.log(`🌍 Allowed Origins: ${allowedOrigins.join(", ")}`);
  });
} catch (err) {
  console.error("❌ Server failed to start:", err);
  process.exit(1);
}
