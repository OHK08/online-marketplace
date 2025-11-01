// const express = require("express");
// const dotenv = require("dotenv");
// const cookieParser = require("cookie-parser");
// const cors = require("cors");
// // const fileUpload = require("express-fileupload");

// // Configs
// const database = require("./config/database");
// const { cloudinaryConnect } = require("./config/cloudinary");

// // Routes
// const authRoutes = require("./routes/authRoutes");
// const userRoutes = require("./routes/userRoutes");
// const artworkRoutes = require("./routes/artworkRoutes");
// const orderRoutes = require("./routes/orderRoutes");
// const likeRoutes = require("./routes/likeRoutes");
// const cartRoutes = require("./routes/cartRoutes");
// const visionRoutes = require("./routes/visionRoutes");
// const searchRoutes = require("./routes/searchRoutes");
// const recommendationRoutes = require("./routes/recommendationRoutes");

// // Initialize app
// dotenv.config();
// const app = express();
// const PORT = process.env.PORT || 5000;

// // ------------------- Database & Cloudinary -------------------
// database.connect();
// cloudinaryConnect();

// // ------------------- Middlewares -------------------
// app.use(express.json());
// app.use(cookieParser());
// app.use(
//   cors({
//     origin: process.env.FRONTEND_URL || "*",
//     credentials: true,
//   })
// );
// // app.use(
// //   fileUpload({
// //     useTempFiles: true,
// //     tempFileDir: "/tmp/",
// //   })
// // );

// // ------------------- Routes -------------------
// app.use("/api/v1/auth", authRoutes);
// app.use("/api/v1/user", userRoutes);
// app.use("/api/v1/artworks", artworkRoutes);
// app.use("/api/v1/order", orderRoutes);
// app.use("/api/v1/like", likeRoutes);
// app.use("/api/v1/cart", cartRoutes);
// app.use("/api/v1/vision", visionRoutes);
// app.use("/api/v1/search-ai/search", searchRoutes);
// app.use("/api/v1/search-ai/recommendations", recommendationRoutes);

// // ------------------- Health Check -------------------
// app.get("/", (req, res) => {
//   return res.json({
//     success: true,
//     message: "Your server is running",
//   });
// });

// // ------------------- Start Server -------------------
// app.listen(PORT, () => {
//   console.log(`Server running on port ${PORT}`);
// });



const express = require("express");
const dotenv = require("dotenv");
const cookieParser = require("cookie-parser");
const cors = require("cors");
const multer = require("multer");
// const fileUpload = require("express-fileupload");

// Configs
const database = require("./config/database");
const { cloudinaryConnect } = require("./config/cloudinary");

// Routes
const authRoutes = require("./routes/authRoutes");
const userRoutes = require("./routes/userRoutes");
const artworkRoutes = require("./routes/artworkRoutes");
const orderRoutes = require("./routes/orderRoutes");
const likeRoutes = require("./routes/likeRoutes");
const cartRoutes = require("./routes/cartRoutes");
const visionRoutes = require("./routes/visionRoutes");
const searchRoutes = require("./routes/searchRoutes");
const recommendationRoutes = require("./routes/recommendationRoutes");

// Initialize app
dotenv.config();
const app = express();
const PORT = process.env.PORT || 5000;

// ------------------- Database & Cloudinary -------------------
database.connect();
cloudinaryConnect();

// ------------------- Middlewares -------------------
app.use(express.json());
app.use(cookieParser());
app.use(
  cors({
    origin: process.env.FRONTEND_URL || "*",
    credentials: true,
  })
);
// app.use(
//   fileUpload({
//     useTempFiles: true,
//     tempFileDir: "/tmp/",
//   })
// );

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

// ------------------- Health Check -------------------
app.get("/", (req, res) => {
  return res.json({
    success: true,
    message: "Your server is running",
  });
});

// ------------------- Error Handling Middleware -------------------
// Handle multer errors
app.use((err, req, res, next) => {
  console.error("=== GLOBAL ERROR HANDLER ===");
  console.error("Error:", err);
  
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
  
  if (err.message && err.message.includes('Invalid file type')) {
    return res.status(400).json({
      success: false,
      message: err.message,
    });
  }
  
  res.status(500).json({
    success: false,
    message: 'Internal server error',
    error: err.message,
  });
});

// ------------------- Start Server -------------------
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});