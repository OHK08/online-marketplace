const multer = require("multer");
const { CloudinaryStorage } = require("multer-storage-cloudinary");
const { cloudinary } = require("../config/cloudinary");

const storage = new CloudinaryStorage({
  cloudinary,
  params: async (req, file) => {
    let folder = "artworks";
    let resourceType = "image";

    if (file.mimetype.startsWith("video")) {
      resourceType = "video";
    }

    // Safer public_id generation - remove special characters
    const timestamp = Date.now();
    const originalName = file.originalname.replace(/\s+/g, '_');
    const nameWithoutExt = originalName.substring(0, originalName.lastIndexOf('.')) || originalName;
    
    // Remove all special characters except underscores and hyphens
    const sanitizedName = nameWithoutExt.replace(/[^a-zA-Z0-9_-]/g, '_');
    
    return {
      folder,
      resource_type: resourceType,
      public_id: `${timestamp}-${sanitizedName}`,
    };
  },
});

const fileFilter = (req, file, cb) => {
  // Accept images and videos
  if (file.mimetype.startsWith('image/') || file.mimetype.startsWith('video/')) {
    cb(null, true);
  } else {
    cb(new Error('Invalid file type. Only images and videos are allowed.'), false);
  }
};

const upload = multer({ 
  storage,
  fileFilter,
  limits: {
    fileSize: 10 * 1024 * 1024, // 10MB limit
  }
});

module.exports = upload;