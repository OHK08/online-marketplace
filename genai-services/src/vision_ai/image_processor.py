from PIL import Image
import io

def preprocess_image(image_bytes: bytes) -> bytes:
    # Open image for validation and potential resizing (mock for now)
    img = Image.open(io.BytesIO(image_bytes))
    # Example: Resize if needed (optional for Day 1)
    # img = img.resize((512, 512))
    return image_bytes  # Return original bytes for mock phase