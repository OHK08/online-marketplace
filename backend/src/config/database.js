const mongoose = require("mongoose");
require("dotenv").config();

exports.connect = () => {
  // FIXED: Changed from MONGODB_URI to match the actual Secret Manager secret name
  // The secret is named "mongodb-connection-string" in GCP Secret Manager
  const mongoURI = process.env.MONGODB_CONNECTION_STRING || process.env.MONGODB_URI;
  
  if (!mongoURI) {
    console.error("❌ ERROR: MONGO_URI is not defined in environment variables");
    process.exit(1);
  }

  mongoose
    .connect(mongoURI, {})
    .then(() => {
      console.log("✅ Database connected successfully");
      console.log(`📊 Database: ${mongoURI.split("@")[1]?.split("/")[0] || "MongoDB"}`);
    })
    .catch((err) => {
      console.error("❌ Database connection failed:", err.message);
      process.exit(1);
    });
};