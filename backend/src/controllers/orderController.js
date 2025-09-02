const { instance } = require("../config/razorpay")
const Order = require("../models/Order");
const Artwork = require("../models/Artwork");
const crypto = require("crypto");


// ------------------ CREATE ORDER ------------------
exports.createOrder = async (req, res) => {
  try {
    const { artworkId, qty } = req.body;
    const buyerId = req.user.id;

    const artwork = await Artwork.findById(artworkId);
    if (!artwork || artwork.status !== "published") {
      return res.status(404).json({ success: false, message: "Artwork not available" });
    }

    if (artwork.quantity < qty) {
      return res.status(400).json({ success: false, message: "Not enough stock" });
    }

    const total = artwork.price * qty;

    // create Razorpay order
    const razorpayOrder = await instance.orders.create({
      amount: total * 100, // paise
      currency: artwork.currency || "INR",
      receipt: `receipt_${Date.now()}`,
    });

    // create order in DB
    const order = await Order.create({
      buyerId,
      sellerId: artwork.artistId,
      items: [
        {
          artworkId: artwork._id,
          titleCopy: artwork.title,
          qty,
          unitPrice: artwork.price,
          currency: artwork.currency,
        },
      ],
      total,
      currency: artwork.currency,
      razorpayOrderId: razorpayOrder.id,
      status: "created",
    });

    res.status(201).json({
      success: true,
      order,
      razorpayOrder,
    });
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

    // decrease stock
    if (order) {
      for (const item of order.items) {
        await Artwork.findByIdAndUpdate(item.artworkId, { $inc: { quantity: -item.qty } });
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
      .sort({ createdAt: -1 });

    res.json({ success: true, count: orders.length, orders });
  } catch (err) {
    console.error("Error in getMyOrders:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
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
    res.status(500).json({ success: false, message: "Internal server error" });
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
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};
