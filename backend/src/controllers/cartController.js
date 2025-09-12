// backend/src/controllers/cartController.js
const mongoose = require("mongoose");
const Cart = require("../models/Cart");
const Artwork = require("../models/Artwork");

// ------------------ ADD TO CART ------------------
exports.addToCart = async (req, res) => {
  try {
    const userId = req.user.id;
    const { artworkId } = req.body;
    let qty = parseInt(req.body.qty, 10);

    if (!artworkId) {
      return res.status(400).json({ success: false, message: "artworkId is required" });
    }
    if (Number.isNaN(qty) || qty <= 0) qty = 1;

    // validate artwork exists
    const artwork = await Artwork.findById(artworkId);
    if (!artwork || artwork.status !== "published") {
      return res.status(404).json({ success: false, message: "Artwork not available" });
    }

    // find or create cart
    let cart = await Cart.findOne({ userId });
    if (!cart) {
      cart = new Cart({ userId, items: [] });
    }

    // check if already in cart
    const existingItem = cart.items.find((it) => it.artworkId.toString() === artworkId.toString());
    if (existingItem) {
      existingItem.qty += qty;
    } else {
      cart.items.push({ artworkId: new mongoose.Types.ObjectId(artworkId), qty });
    }

    await cart.save();
    await cart.populate("items.artworkId");

    // calculate total
    const total = cart.items.reduce((sum, item) => {
      return sum + (item.artworkId?.price || 0) * item.qty;
    }, 0);

    res.json({ success: true, message: "Cart updated", cart, total });
  } catch (err) {
    console.error("Error in addToCart:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};

// ------------------ REMOVE FROM CART ------------------
exports.removeFromCart = async (req, res) => {
  try {
    const userId = req.user.id;
    const { artworkId } = req.params;

    let cart = await Cart.findOneAndUpdate(
      { userId },
      { $pull: { items: { artworkId: artworkId } } },
      { new: true }
    ).populate("items.artworkId");

    if (!cart) cart = { items: [] };

    const total = cart.items?.reduce((sum, item) => sum + (item.artworkId?.price || 0) * item.qty, 0) || 0;

    res.json({ success: true, message: "Item removed from cart", cart, total });
  } catch (err) {
    console.error("Error in removeFromCart:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};

// ------------------ GET CART ------------------
exports.getCart = async (req, res) => {
  try {
    const userId = req.user.id;
    let cart = await Cart.findOne({ userId }).populate("items.artworkId");

    if (!cart) {
      return res.json({ success: true, message: "Cart is empty", cart: { items: [] }, total: 0 });
    }

    const total = cart.items.reduce((sum, item) => sum + (item.artworkId?.price || 0) * item.qty, 0);

    res.json({ success: true, cart, total });
  } catch (err) {
    console.error("Error in getCart:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};

// ------------------ UPDATE CART ITEM QUANTITY ------------------
exports.updateCartItem = async (req, res) => {
  try {
    const userId = req.user.id;
    const { artworkId, qty } = req.body;

    if (!artworkId || qty === undefined) {
      return res.status(400).json({ success: false, message: "artworkId and qty are required" });
    }
    if (qty < 1) {
      return res.status(400).json({ success: false, message: "Quantity must be at least 1" });
    }

    let cart = await Cart.findOne({ userId });
    if (!cart) return res.status(404).json({ success: false, message: "Cart not found" });

    const item = cart.items.find((it) => it.artworkId.toString() === artworkId);
    if (!item) return res.status(404).json({ success: false, message: "Item not in cart" });

    item.qty = qty;
    await cart.save();
    await cart.populate("items.artworkId");

    const total = cart.items.reduce((sum, item) => sum + (item.artworkId?.price || 0) * item.qty, 0);

    res.json({ success: true, message: "Cart updated", cart, total });
  } catch (err) {
    console.error("Error in updateCartItem:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};

// ------------------ VERIFY CART PAYMENT ------------------
exports.verifyCartPayment = async (req, res) => {
  try {
    const { razorpayOrderId, razorpayPaymentId, razorpaySignature } = req.body;

    const body = razorpayOrderId + "|" + razorpayPaymentId;
    const expectedSignature = crypto
      .createHmac("sha256", process.env.RAZORPAY_SECRET)
      .update(body.toString())
      .digest("hex");

    if (expectedSignature !== razorpaySignature) {
      return res.status(400).json({
        success: false,
        message: "Payment verification failed",
      });
    }

    // update order
    const order = await Order.findOneAndUpdate(
      { razorpayOrderId },
      {
        razorpayPaymentId,
        razorpaySignature,
        status: "paid",
      },
      { new: true }
    );

    if (!order) {
      return res.status(404).json({ success: false, message: "Order not found" });
    }

    // reduce stock for each item
    for (const item of order.items) {
      const updatedArtwork = await Artwork.findByIdAndUpdate(
        item.artworkId,
        { $inc: { quantity: -item.qty } },
        { new: true }
      );
      if (updatedArtwork && updatedArtwork.quantity <= 0) {
        updatedArtwork.status = "removed"; // or "out_of_stock"
        await updatedArtwork.save();
      }
    }

    res.json({ success: true, message: "Cart payment verified", order });
  } catch (err) {
    console.error("Error in verifyCartPayment:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};