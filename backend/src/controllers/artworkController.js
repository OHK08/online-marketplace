// backend/src/controllers/artworkController.js
const Artwork = require("../models/Artwork");
const User = require("../models/User");
const mongoose = require("mongoose");
const { cloudinary } = require("../config/cloudinary");
const giftAIService = require("../services/giftAIService");

// ------------------ CREATE ARTWORK ------------------
exports.createArtwork = async (req, res) => {
  try {
    console.log("=== CREATE ARTWORK DEBUG ===");
    console.log("Request body:", JSON.stringify(req.body, null, 2));
    console.log("Request files:", req.files);
    console.log("User ID:", req.user?.id);

    const { title, description, price, currency, quantity, status } = req.body;

    // Validation
    if (!title || !price) {
      console.log("Validation failed: missing title or price");
      return res.status(400).json({
        success: false,
        message: "Title and price are required",
      });
    }

    // Handle tags - completely optional
    let tags = [];
    if (req.body.tags !== undefined && req.body.tags !== null && req.body.tags !== '') {
      const tagsInput = req.body.tags;
      console.log("Tags input:", tagsInput, "Type:", typeof tagsInput);
      
      if (Array.isArray(tagsInput)) {
        tags = tagsInput.filter(tag => tag && tag.trim() !== '');
      } else if (typeof tagsInput === 'string') {
        const trimmed = tagsInput.trim();
        if (trimmed !== '') {
          if (trimmed.startsWith('[')) {
            try {
              tags = JSON.parse(trimmed);
              if (!Array.isArray(tags)) {
                tags = [trimmed];
              }
            } catch (e) {
              console.log("Failed to parse tags as JSON, treating as single tag");
              tags = [trimmed];
            }
          } else {
            tags = [trimmed];
          }
        }
      }
    } else {
      console.log("Tags not provided, using empty array");
    }

    console.log("Parsed tags:", tags);

    // Process uploaded files with better error handling
    let media = [];
    if (req.files && req.files.length > 0) {
      console.log("Processing files...");
      
      media = req.files.map((file) => {
        console.log("File details:", {
          path: file.path,
          filename: file.filename,
          mimetype: file.mimetype,
          size: file.size
        });
        
        // Cloudinary provides the full URL in file.path
        if (!file.path) {
          throw new Error(`File upload failed: missing path for ${file.originalname}`);
        }
        
        return {
          url: file.path, // Cloudinary URL
          type: file.mimetype.startsWith("video") ? "video" : "image",
          sizeBytes: file.size,
          storageKey: file.filename, // Cloudinary public_id
        };
      });
      
      console.log("Successfully processed media:", media);
    } else {
      console.log("No files uploaded");
    }

    // Get artist name for denormalization
    let artistName = '';
    try {
      const artist = await User.findById(req.user.id).select('name');
      if (!artist) {
        return res.status(404).json({
          success: false,
          message: "Artist not found",
        });
      }
      artistName = artist.name || '';
      console.log("Artist name:", artistName);
    } catch (error) {
      console.error("Error fetching artist:", error);
      return res.status(500).json({
        success: false,
        message: "Error fetching artist details",
        error: error.message,
      });
    }

    // Prepare artwork data
    const artworkData = {
      artistId: req.user.id,
      title: title.trim(),
      description: description ? description.trim() : '',
      price: Number(price),
      currency: currency || "INR",
      quantity: quantity ? Number(quantity) : 1,
      status: status || "draft",
      tags: tags,
      artistName: artistName,
      media: media,
      updatedAt_timestamp: Date.now(),
    };

    console.log("Creating artwork with data:", JSON.stringify(artworkData, null, 2));

    // Create artwork
    const artwork = await Artwork.create(artworkData);

    console.log("Artwork created successfully:", artwork._id);

    // 🎁 AUTO-INDEX: Index artwork in AI vector store if published
    if (artwork.status === "published") {
      try {
        await giftAIService.indexArtwork(artwork);
        console.log(`✅ Artwork ${artwork._id} indexed in AI vector store`);
      } catch (error) {
        console.error(`⚠️ Failed to index artwork ${artwork._id}:`, error.message);
        // Don't fail the request if indexing fails
      }
    }

    res.status(201).json({
      success: true,
      message: "Artwork posted successfully",
      artwork,
    });
  } catch (err) {
    console.error("=== ERROR CREATING ARTWORK ===");
    console.error("Error name:", err.name);
    console.error("Error message:", err.message);
    console.error("Error stack:", err.stack);
    
    // Cleanup uploaded files if artwork creation fails
    if (req.files && req.files.length > 0) {
      console.log("Attempting to cleanup uploaded files...");
      for (const file of req.files) {
        if (file.filename) {
          try {
            await cloudinary.uploader.destroy(file.filename);
            console.log(`Deleted file: ${file.filename}`);
          } catch (cleanupErr) {
            console.error("Error cleaning up file:", cleanupErr.message);
          }
        }
      }
    }
    
    res.status(500).json({
      success: false,
      message: "Internal server error while creating artwork",
      error: err.message,
      stack: process.env.NODE_ENV === 'development' ? err.stack : undefined,
    });
  }
};

// ------------------ GET ALL ARTWORKS ------------------
exports.getAllArtworks = async (req, res) => {
  try {
    const artworks = await Artwork.find({ status: "published" })
      .populate("artistId", "name email avatarUrl")
      .sort({ createdAt: -1 });

    res.json({
      success: true,
      count: artworks.length,
      artworks,
    });
  } catch (err) {
    console.error("Error fetching artworks:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while fetching artworks",
    });
  }
};

// ------------------ GET ARTWORK BY ID ------------------
exports.getArtworkById = async (req, res) => {
  try {
    const { id } = req.params;

    if (!mongoose.Types.ObjectId.isValid(id)) {
      return res.status(400).json({ success: false, message: "Invalid ID" });
    }

    const artwork = await Artwork.findById(id).populate(
      "artistId",
      "name email avatarUrl"
    );

    if (!artwork) {
      return res.status(404).json({ success: false, message: "Artwork not found" });
    }

    res.json({
      success: true,
      artwork,
    });
  } catch (err) {
    console.error("Error fetching artwork by ID:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while fetching artwork",
    });
  }
};

// ------------------ DELETE ARTWORK ------------------
exports.deleteArtwork = async (req, res) => {
  try {
    const { id } = req.params;

    const artwork = await Artwork.findById(id);

    if (!artwork) {
      return res.status(404).json({ success: false, message: "Artwork not found" });
    }

    if (artwork.artistId.toString() !== req.user.id) {
      return res.status(403).json({ success: false, message: "Unauthorized" });
    }

    await artwork.deleteOne();

    // Note: Vector store cleanup would require additional API endpoint
    // For now, deleted items will simply not be returned in searches

    res.json({
      success: true,
      message: "Artwork deleted successfully",
    });
  } catch (err) {
    console.error("Error deleting artwork:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while deleting artwork",
    });
  }
};

// ------------------ GET USER'S ARTWORKS ------------------
exports.myArtworks = async (req, res) => {
  try {
    const artworks = await Artwork.find({ artistId: req.user.id }).sort({
      createdAt: -1,
    });

    res.json({
      success: true,
      count: artworks.length,
      artworks,
    });
  } catch (err) {
    console.error("Error fetching user's artworks:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while fetching user's artworks",
    });
  }
};

// ------------------ UPDATE ARTWORK ------------------
exports.updateArtwork = async (req, res) => {
  try {
    const { id } = req.params;
    const { title, description, price, currency, quantity, status } = req.body;
    
    const artwork = await Artwork.findById(id);
    if (!artwork) {
      return res.status(404).json({ success: false, message: "Artwork not found" });
    }
    
    if (artwork.artistId.toString() !== req.user.id) {
      return res.status(403).json({ success: false, message: "Unauthorized" });
    }
    
    if (artwork.status !== "draft") {
      return res.status(400).json({
        success: false,
        message: "Only artworks in draft state can be edited",
      });
    }
    
    if (title) artwork.title = title.trim();
    if (description !== undefined) artwork.description = description.trim();
    if (price) artwork.price = Number(price);
    if (currency) artwork.currency = currency;
    if (quantity) artwork.quantity = Number(quantity);
    
    // Handle tags
    if (req.body.tags !== undefined) {
      let tags = [];
      const tagsInput = req.body.tags;
      
      if (tagsInput === null || tagsInput === '') {
        tags = [];
      } else if (Array.isArray(tagsInput)) {
        tags = tagsInput.filter(tag => tag && tag.trim() !== '');
      } else if (typeof tagsInput === 'string') {
        const trimmed = tagsInput.trim();
        if (trimmed === '') {
          tags = [];
        } else if (trimmed.startsWith('[')) {
          try {
            tags = JSON.parse(trimmed);
            if (!Array.isArray(tags)) {
              tags = [trimmed];
            }
          } catch (e) {
            tags = [trimmed];
          }
        } else {
          tags = [trimmed];
        }
      }
      
      artwork.tags = tags;
    }
    
    // Track status change for AI indexing
    const wasPublished = artwork.status === "published";
    if (status) artwork.status = status;
    const isNowPublished = artwork.status === "published";
    
    artwork.updatedAt_timestamp = Date.now();
    
    await artwork.save();
    
    // 🎁 AUTO-INDEX: Index if newly published or re-index if already published
    if (isNowPublished && !wasPublished) {
      try {
        await giftAIService.indexArtwork(artwork);
        console.log(`✅ Artwork ${artwork._id} indexed in AI vector store`);
      } catch (error) {
        console.error(`⚠️ Failed to index artwork ${artwork._id}:`, error.message);
      }
    } else if (isNowPublished && wasPublished) {
      // Re-index if already published (content changed)
      try {
        await giftAIService.indexArtwork(artwork);
        console.log(`♻️ Artwork ${artwork._id} re-indexed in AI vector store`);
      } catch (error) {
        console.error(`⚠️ Failed to re-index artwork ${artwork._id}:`, error.message);
      }
    }
    
    res.json({
      success: true,
      message: "Artwork updated successfully",
      artwork,
    });
  } catch (err) {
    console.error("Error updating artwork:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while updating artwork",
      error: err.message,
    });
  }
};

// ------------------ RESTOCK ARTWORK ------------------
exports.restockArtwork = async (req, res) => {
  try {
    const { id } = req.params;
    const { quantity } = req.body;

    if (!quantity || quantity <= 0) {
      return res.status(400).json({
        success: false,
        message: "Quantity must be greater than 0",
      });
    }

    const artwork = await Artwork.findById(id);

    if (!artwork) {
      return res.status(404).json({ success: false, message: "Artwork not found" });
    }

    if (artwork.artistId.toString() !== req.user.id) {
      return res.status(403).json({ success: false, message: "Unauthorized" });
    }

    artwork.quantity += Number(quantity);

    if (artwork.status === "out_of_stock" || artwork.status === "removed") {
      artwork.status = "published";
      
      // 🎁 AUTO-INDEX: Re-index when restocking
      try {
        await giftAIService.indexArtwork(artwork);
        console.log(`♻️ Artwork ${artwork._id} re-indexed after restocking`);
      } catch (error) {
        console.error(`⚠️ Failed to re-index artwork ${artwork._id}:`, error.message);
      }
    }

    artwork.updatedAt_timestamp = Date.now();

    await artwork.save();

    res.json({
      success: true,
      message: "Artwork restocked successfully",
      artwork,
    });
  } catch (err) {
    console.error("Error restocking artwork:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while restocking artwork",
      error: err.message,
    });
  }
};