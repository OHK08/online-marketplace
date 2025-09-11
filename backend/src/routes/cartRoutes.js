const express = require("express");
const router = express.Router();
const cartController = require("../controllers/cartController");
const authMiddleware = require("../middlewares/authMiddleware");

router.post("/add", authMiddleware, cartController.addToCart);
router.delete("/remove/:artworkId", authMiddleware, cartController.removeFromCart);
router.get("/", authMiddleware, cartController.getCart);
router.post("/checkout", authMiddleware, cartController.createOrderFromCart);
router.put("/update", authMiddleware, cartController.updateCartItem);

module.exports = router;
