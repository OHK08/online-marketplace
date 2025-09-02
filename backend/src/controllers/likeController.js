const Like = require("../models/Like");
const Artwork = require("../models/Artwork");

// ------------------ LIKE / UNLIKE ARTWORK ------------------
exports.likeArtwork = async (req, res) => {
  try {
    const { artworkId } = req.params;
    const userId = req.user.id;

    // check if already liked
    const existingLike = await Like.findOne({ userId, artworkId });

    if (existingLike) {
      // Unlike
      await existingLike.deleteOne();
      await Artwork.findByIdAndUpdate(artworkId, { $inc: { likeCount: -1 } });

      return res.json({
        success: true,
        message: "Artwork unliked",
      });
    } else {
      // Like
      await Like.create({ userId, artworkId });
      await Artwork.findByIdAndUpdate(artworkId, { $inc: { likeCount: 1 } });

      return res.json({
        success: true,
        message: "Artwork liked",
      });
    }
  } catch (err) {
    console.error("Error in likeArtwork:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while liking artwork",
    });
  }
};

// ------------------ GET USER'S LIKED ARTWORKS ------------------
exports.getLikedArtworks = async (req, res) => {
  try {
    const userId = req.user.id;

    const likes = await Like.find({ userId }).populate("artworkId");
    const likedArtworks = likes.map((l) => l.artworkId);

    res.json({
      success: true,
      count: likedArtworks.length,
      artworks: likedArtworks,
    });
  } catch (err) {
    console.error("Error in getLikedArtworks:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while fetching liked artworks",
    });
  }
};
