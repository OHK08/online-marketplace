// backend/src/controllers/cartController.js
const mongoose = require("mongoose");
const Cart = require("../models/Cart");
const Artwork = require("../models/Artwork");
const Order = require("../models/Order");
const { instance } = require("../config/razorpay"); // make sure your config exports { instance }
const crypto = require("crypto");

//Add item to cart

exports.addToCart = async (req, res) => {
  try {
    const userId = req.user.id;
    const { artworkId } = req.body;
    let qty = req.body.qty;

    // normalize qty to integer
    qty = parseInt(qty, 10);
    if (Number.isNaN(qty) || qty <= 0) qty = 1;

    if (!artworkId) {
      return res.status(400).json({ success: false, message: "artworkId is required" });
    }

    // ensure artwork exists
    const artwork = await Artwork.findById(artworkId);
    if (!artwork) {
      return res.status(404).json({ success: false, message: "Artwork not found" });
    }

    // ensure user has a cart
    let cart = await Cart.findOne({ userId });
    if (!cart) {
      cart = new Cart({ userId, items: [] });
    }

    // find existing item
    const existingItem = cart.items.find((it) => it.artworkId.toString() === artworkId.toString());
    if (existingItem) {
      // numeric increase
      existingItem.qty = Number(existingItem.qty) + Number(qty);
    } else {
      cart.items.push({
        artworkId: new mongoose.Types.ObjectId(artworkId),
        qty: Number(qty),
      });
    }

    await cart.save();

    let total = 0;
    for (const item of cart.items) {
    const artwork = await Artwork.findById(item.artworkId);
    if (artwork) {
        total += artwork.price * item.qty;
    }
    }

    res.json({
    success: true,
    message: "Item added to cart",  // or "Cart updated"
    cart,
    total,
    });

    // populate for response
    await cart.populate("items.artworkId");

    res.json({ success: true, message: "Item added to cart", cart });
  } catch (err) {
    console.error("Error in addToCart:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};

//Remove an artwork from cart

exports.removeFromCart = async (req, res) => {
  try {
    const userId = req.user.id;
    const { artworkId } = req.params;

    const cart = await Cart.findOneAndUpdate(
      { userId },
      { $pull: { items: { artworkId: artworkId } } },
      { new: true }
    );

    if (cart) {
      await cart.populate("items.artworkId");
    }

    res.json({ success: true, message: "Item removed from cart", cart: cart || { items: [] } });
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
      return res.json({ success: true, message: "Cart is empty", cart: { items: [], total: 0 } });
    }

    // calculate total
    let total = 0;
    cart.items.forEach((item) => {
      if (item.artworkId && item.artworkId.price) {
        total += item.artworkId.price * item.qty;
      }
    });

    res.json({
      success: true,
      cart,
      total,
    });
  } catch (err) {
    console.error("Error in getCart:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};


/**
 * Checkout cart → create orders grouped by seller.
 * POST /cart/checkout
 *
 * Behavior:
 * - Groups cart items by artwork.artistId (seller)
 * - For each seller, creates a Razorpay order and a DB Order
 * - Clears the cart after creating orders
 * - Returns array of created orders and corresponding razorpayOrders
 *
 * NOTE: Frontend must handle payment per razorpayOrder returned (one payment per seller).
 */
exports.createOrderFromCart = async (req, res) => {
  try {
    const userId = req.user.id;
    const cart = await Cart.findOne({ userId }).populate("items.artworkId");

    if (!cart || cart.items.length === 0) {
      return res.status(400).json({ success: false, message: "Cart is empty" });
    }

    // Group items by sellerId (artistId)
    const groups = {}; // sellerId -> [cartItem, ...]
    for (const item of cart.items) {
      const artwork = item.artworkId;
      if (!artwork) {
        return res.status(400).json({ success: false, message: "Invalid artwork in cart" });
      }
      const sellerId = artwork.artistId.toString();
      if (!groups[sellerId]) groups[sellerId] = [];
      groups[sellerId].push(item);
    }

    const created = []; // will hold { sellerId, order, razorpayOrder }

    // For each seller group, validate and create order + razorpay order
    for (const sellerId of Object.keys(groups)) {
      const groupItems = groups[sellerId];
      let orderItems = [];
      let total = 0;

      // validate stock and build orderItems
      for (const cItem of groupItems) {
        const art = await Artwork.findById(cItem.artworkId._id); // get fresh qty
        if (!art || art.status !== "published") {
          return res.status(404).json({ success: false, message: `Artwork ${cItem.artworkId._id} not available` });
        }
        if (art.quantity < cItem.qty) {
          return res.status(400).json({ success: false, message: `Not enough stock for ${art.title}` });
        }

        orderItems.push({
          artworkId: art._id,
          titleCopy: art.title,
          qty: cItem.qty,
          unitPrice: art.price,
          currency: art.currency,
        });

        total += art.price * cItem.qty;
      }

      // create razorpay order for this seller group
      const razorpayOrder = await instance.orders.create({
        amount: Math.round(total * 100), // paise and rounding
        currency: "INR",
        receipt: `cart_${userId}_${Date.now()}_${sellerId}`,
      });

      // save order in DB
      const order = await Order.create({
        buyerId: userId,
        sellerId,
        items: orderItems,
        total,
        currency: "INR",
        razorpayOrderId: razorpayOrder.id,
        status: "created",
      });

      created.push({ sellerId, order, razorpayOrder });
    }

    // clear cart
    cart.items = [];
    await cart.save();

    // return created orders so frontend knows which razorpay orders to pay
    res.status(201).json({ success: true, created });
  } catch (err) {
    console.error("Error in createOrderFromCart:", err);
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
    if (!cart) {
      return res.status(404).json({ success: false, message: "Cart not found" });
    }

    const itemIndex = cart.items.findIndex((it) => it.artworkId.toString() === artworkId);
    if (itemIndex === -1) {
      return res.status(404).json({ success: false, message: "Item not found in cart" });
    }

    cart.items[itemIndex].qty = Number(qty);
    await cart.save();

    // inside addToCart and updateCartItem after cart.save()
    let total = 0;
    for (const item of cart.items) {
    const artwork = await Artwork.findById(item.artworkId);
    if (artwork) {
        total += artwork.price * item.qty;
    }
    }

    res.json({
    success: true,
    message: "Item added to cart",  // or "Cart updated"
    cart,
    total,
    });


    res.json({ success: true, message: "Cart updated", cart });
  } catch (err) {
    console.error("Error in updateCartItem:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};
