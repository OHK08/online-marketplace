const User = require("../models/User");

// ------------------ GET PROFILE ------------------
exports.getProfile = async (req, res) => {
  try {
    const userId = req.user.id;

    const user = await User.findById(userId)
      .select("-password")
      .populate("likes", "title price media");

    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    res.json({ success: true, user });
  } catch (err) {
    console.error("Error in getProfile:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};

// ------------------ UPDATE PROFILE ------------------
exports.updateProfile = async (req, res) => {
  try {
    const userId = req.user.id;
    const { name, phone, avatarUrl, bio, region } = req.body;

    const user = await User.findByIdAndUpdate(
      userId,
      {
        $set: {
          name,
          phone,
          avatarUrl,
          bio,
          region,
          lastSeen: new Date(),
        },
      },
      { new: true }
    ).select("-password");

    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    res.json({ success: true, message: "Profile updated", user });
  } catch (err) {
    console.error("Error in updateProfile:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};

// ------------------ DELETE ACCOUNT ------------------
exports.deleteAccount = async (req, res) => {
  try {
    const userId = req.user.id;

    const user = await User.findByIdAndDelete(userId);
    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    res.json({ success: true, message: "Account deleted successfully" });
  } catch (err) {
    console.error("Error in deleteAccount:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};
