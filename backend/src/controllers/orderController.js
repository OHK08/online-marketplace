const { instance } = require("../config/razorpay")
const Order = require("../models/Order");
const Artwork = require("../models/Artwork");
const crypto = require("crypto");


// ------------------ CREATE ORDER (MULTIPLE ITEMS) ------------------
exports.createOrder = async (req, res) => {
  try {
    const { items } = req.body; // [{artworkId, qty}, ...]
    const buyerId = req.user.id;

    if (!items || !Array.isArray(items) || items.length === 0) {
      return res.status(400).json({ success: false, message: "No items in order" });
    }

    let orderItems = [];
    let total = 0;
    let sellerId = null;

    // Validate each artwork
    for (const { artworkId, qty } of items) {
      const artwork = await Artwork.findById(artworkId);

      if (!artwork || artwork.status !== "published") {
        return res.status(404).json({ success: false, message: `Artwork ${artworkId} not available` });
      }

      if (artwork.quantity < qty) {
        return res.status(400).json({ success: false, message: `Not enough stock for ${artwork.title}` });
      }

      if (!sellerId) sellerId = artwork.artistId;

      orderItems.push({
        artworkId: artwork._id,
        titleCopy: artwork.title,
        qty,
        unitPrice: artwork.price,
        currency: artwork.currency,
      });

      total += artwork.price * qty;
    }

    // Create Razorpay order
    const razorpayOrder = await instance.orders.create({
      amount: total * 100,
      currency: "INR",
      receipt: `receipt_${Date.now()}`,
    });

    // Save in DB
    const order = await Order.create({
      buyerId,
      sellerId,
      items: orderItems,
      total,
      currency: "INR",
      razorpayOrderId: razorpayOrder.id,
      status: "created",
    });

    res.status(201).json({ success: true, order, razorpayOrder });
  } catch (err) {
    console.error("Error in createOrder:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};


// ------------------ VERIFY PAYMENT ------------------
exports.verifyPayment = async (req, res) => {
  try {
    const { razorpayOrderId, razorpayPaymentId, razorpaySignature } = req.body;

    const body = razorpayOrderId + "|" + razorpayPaymentId;
    const expectedSignature = crypto
      .createHmac("sha256", process.env.RAZORPAY_KEY_SECRET)
      .update(body.toString())
      .digest("hex");

    if (expectedSignature !== razorpaySignature) {
      return res.status(400).json({ success: false, message: "Payment verification failed" });
    }

    // update order as paid
    const order = await Order.findOneAndUpdate(
      { razorpayOrderId },
      { razorpayPaymentId, razorpaySignature, status: "paid" },
      { new: true }
    );

    // reduce stock if payment successful
    if (order) {
      for (const item of order.items) {
        const updatedArtwork = await Artwork.findByIdAndUpdate(
          item.artworkId,
          { $inc: { quantity: -item.qty } },
          { new: true }
        );

        // if stock reaches 0 → mark as out of stock
        if (updatedArtwork && updatedArtwork.quantity <= 0) {
          updatedArtwork.status = "removed"; // or "out_of_stock" if you add new enum
          await updatedArtwork.save();
        }
      }
    }

    res.json({ success: true, message: "Payment verified", order });
  } catch (err) {
    console.error("Error in verifyPayment:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};



// ------------------ GET MY ORDERS (BUYER) ------------------
exports.getMyOrders = async (req, res) => {
  try {
    const buyerId = req.user.id;
    const orders = await Order.find({ buyerId })
      .populate("items.artworkId")
      .populate("sellerId", "name email")
      .sort({ createdAt: -1 });

    res.json({ success: true, count: orders.length, orders });
  } catch (err) {
    console.error("Error in getMyOrders:", err);
    res.status(500).json({ success: false, message: "Internal server error while getting my orders(buyer)" });
  }
};


// ------------------ GET SALES (SELLER) ------------------
exports.getSales = async (req, res) => {
  try {
    const sellerId = req.user.id;
    const sales = await Order.find({ sellerId })
      .populate("items.artworkId")
      .sort({ createdAt: -1 });

    res.json({ success: true, count: sales.length, sales });
  } catch (err) {
    console.error("Error in getSales:", err);
    res.status(500).json({ success: false, message: "Internal server error while getting sales (seller)" });
  }
};

// ------------------ UPDATE ORDER STATUS (Seller only) ------------------
exports.updateOrderStatus = async (req, res) => {
  try {
    const { id } = req.params;
    const { status } = req.body;
    const sellerId = req.user.id;

    const order = await Order.findById(id);
    if (!order) {
      return res.status(404).json({ success: false, message: "Order not found" });
    }

    if (order.sellerId.toString() !== sellerId) {
      return res.status(403).json({ success: false, message: "Unauthorized" });
    }

    order.status = status;
    await order.save();

    res.json({ success: true, message: "Order status updated", order });
  } catch (err) {
    console.error("Error in updateOrderStatus:", err);
    res.status(500).json({ success: false, message: "Internal server error while updating order status" });
  }
};
