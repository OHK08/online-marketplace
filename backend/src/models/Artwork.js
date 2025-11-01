// backend/src/models/Artwork.js
const mongoose = require('mongoose');
const { Schema } = mongoose;

const MediaSchema = new Schema({
  url: { type: String, required: true },
  type: { type: String, enum: ['image', 'video'], default: 'image' },
  sizeBytes: Number,
  storageKey: String,
}, { _id: false });

const ArtworkSchema = new Schema({
  artistId: {
    type: Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true,
  },
  title: { type: String, required: true, trim: true },
  description: { type: String },
  media: { type: [MediaSchema], default: [] },
  price: { type: Number, required: true },
  currency: { type: String, default: 'INR' },
  quantity: { type: Number, default: 1 },
  status: {
    type: String,
    enum: ['draft', 'published', 'removed', 'out_of_stock'],
    default: 'draft',
  },
  likeCount: { type: Number, default: 0 },

  // Denormalized fields for search and recommendations
  artistName: { 
    type: String, 
    trim: true,
    index: true 
  },
  purchaseCount: { 
    type: Number, 
    default: 0,
    index: true 
  },

  // Tags for festive filtering
  tags: {
    type: [String],
    default: [],
    index: true,
  },

  // Unix timestamp in milliseconds for update job
  updatedAt_timestamp: {
    type: Number,
    index: true,
  },
}, { timestamps: true });

ArtworkSchema.index({ title: 'text', description: 'text', tags: 'text' });

module.exports = mongoose.model('Artwork', ArtworkSchema);