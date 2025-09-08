// backend/src/models/Order.js
const mongoose = require('mongoose');
const { Schema } = mongoose;

const OrderItemSchema = new Schema({
    artworkId: { 
        type: Schema.Types.ObjectId, 
        ref: 'Artwork' 
    },
    titleCopy: String,
    qty: { 
        type: Number, 
        default: 1 
    },
    unitPrice: Number,
    currency: { 
        type: String, 
        default: 'INR' 
    }
}, { _id: false });

const OrderSchema = new Schema({
    buyerId: { 
        type: Schema.Types.ObjectId, 
        ref: 'User', 
        required: true 
    },
    sellerId: { 
        type: Schema.Types.ObjectId, 
        ref: 'User', 
        required: true 
    },
    items: { 
        type: [OrderItemSchema], 
        default: [] 
    },
    total: { 
        type: Number, 
        required: true 
    },
    currency: { 
        type: String, 
        default: 'INR' 
    },

    // Razorpay specific fields
    razorpayOrderId: { type: String },   // order created in Razorpay
    razorpayPaymentId: { type: String }, // payment id after success
    razorpaySignature: { type: String }, // for verification

    status: { 
        type: String, 
        enum: ['created','pending','paid','failed','shipped','out_for_delivery','delivered','cancelled'], 
        default: 'created' 
    }
}, { timestamps: true });

OrderSchema.index({ buyerId: 1 });
OrderSchema.index({ sellerId: 1 });

module.exports = mongoose.model('Order', OrderSchema);
