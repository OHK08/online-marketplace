# ============================================================================
# FILE: utils.py
# ============================================================================
"""
Utility functions for veo-generator Cloud Run Job.
Handles MongoDB connection, Veo video generation, and GCS operations.
"""
import requests
import base64
import time
import json
from datetime import datetime
from typing import List, Dict, Optional
from pymongo import MongoClient
from bson import ObjectId
from google.cloud import secretmanager
from google.auth import default
from google.auth.transport.requests import Request
import config


def get_access_token() -> str:
    """
    Get a valid access token for Google Cloud API authentication.
    
    Returns:
        Access token string
    """
    credentials, project = default()
    credentials.refresh(Request())
    return credentials.token


def get_secret(secret_name: str) -> str:
    """
    Fetch a secret from Google Secret Manager.
    
    Args:
        secret_name: Name of the secret (e.g., 'mongodb-connection-string')
    
    Returns:
        The secret value as a string
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{config.GCP_PROJECT_ID}/secrets/{secret_name}/versions/latest"
    
    try:
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        print(f"✅ Successfully retrieved secret: {secret_name}")
        return secret_value
    except Exception as e:
        print(f"❌ Error retrieving secret {secret_name}: {e}")
        raise


def get_mongo_client() -> MongoClient:
    """
    Create and return a MongoDB client connection.
    
    Returns:
        Connected MongoClient instance
    """
    try:
        mongodb_uri = get_secret(config.MONGODB_SECRET_NAME)
        client = MongoClient(mongodb_uri)
        # Test the connection
        client.admin.command('ping')
        print(f"✅ Connected to MongoDB database: {config.MONGODB_DATABASE}")
        return client
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        raise


def fetch_artworks_to_process(mongo_client: MongoClient) -> List[Dict]:
    """
    Query MongoDB for artworks that need video generation.
    
    Args:
        mongo_client: Connected MongoDB client
    
    Returns:
        List of artwork documents
    """
    db = mongo_client[config.MONGODB_DATABASE]
    collection = db["artworks"]
    
    # Query for artworks without videos and not already marked as skipped
    query = {
        "generatedVideoUrl": {"$exists": False},
        "videoGenerationStatus": {"$ne": "skipped_no_image"}
    }
    
    if config.TEST_MODE:
        # In test mode, limit to 2 artworks for faster testing
        limit = 2
        print(f"⚠️  TEST MODE: Processing only {limit} artworks")
    else:
        limit = config.VIDEO_BATCH_SIZE
        print(f"📊 Processing {limit} artworks")
    
    try:
        artworks = list(
            collection.find(query)
            .sort("purchaseCount", -1)  # Most popular first
            .limit(limit)
        )
        
        print(f"✅ Found {len(artworks)} artworks to process")
        
        if len(artworks) == 0:
            print("⚠️  No artworks found without videos. All done!")
        
        return artworks
    except Exception as e:
        print(f"❌ Error fetching artworks: {e}")
        raise


def download_image_as_base64(image_url: str) -> tuple[str, str]:
    """
    Download an image and return its base64 content along with the MIME type.
    """
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        # Try to get MIME type from headers
        mime_type = response.headers.get("Content-Type")

        # Fallback: guess from URL extension if header missing
        if not mime_type:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(image_url)

        if not mime_type:
            raise ValueError(f"Could not determine MIME type for image: {image_url}")

        image_base64 = base64.b64encode(response.content).decode("utf-8")
        return image_base64, mime_type

    except Exception as e:
        print(f"❌ Error downloading image from {image_url}: {e}")
        raise


def mark_artwork_as_skipped(mongo_client: MongoClient, artwork_id: str, reason: str):
    """
    Mark an artwork as skipped in MongoDB to prevent reprocessing.
    
    Args:
        mongo_client: Connected MongoDB client
        artwork_id: ID of the artwork document
        reason: Reason for skipping (e.g., 'no_image')
    """
    db = mongo_client[config.MONGODB_DATABASE]
    collection = db["artworks"]
    
    try:
        collection.update_one(
            {"_id": ObjectId(artwork_id)},
            {"$set": {
                "videoGenerationStatus": f"skipped_{reason}",
                "videoUpdatedAt": datetime.utcnow()
            }}
        )
        print(f"⚠️  Marked artwork {artwork_id} as skipped ({reason})")
    except Exception as e:
        print(f"❌ Error marking artwork as skipped: {e}")


def start_video_generation(prompt: str, image_base64: Optional[str], mime_type: Optional[str], output_uri: str) -> Optional[str]:
    """
    Start a video generation operation using Veo API.
    
    Args:
        prompt: Text prompt for video generation
        image_base64: Optional base64-encoded image for image-to-video
        output_uri: GCS URI for output storage (e.g., gs://bucket/folder/)
    
    Returns:
        Operation name/ID if successful, None otherwise
    """
    try:
        access_token = get_access_token()
        
        url = f"{config.VEO_API_ENDPOINT}/projects/{config.GCP_PROJECT_ID}/locations/{config.VEO_LOCATION}/{config.VEO_MODEL_ID}:predictLongRunning"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # Build request body
        instance = {"prompt": prompt}
        if image_base64:
            instance["image"] = {
                "bytesBase64Encoded": image_base64,
                "mimeType": mime_type  # ✅ include mime type here
            }
        
        request_body = {
            "instances": [instance],
            "parameters": {
                "storageUri": output_uri,
                "sampleCount": config.VIDEO_SAMPLE_COUNT,
                "resolution": config.VIDEO_RESOLUTION,
                "generateAudio": config.VIDEO_GENERATE_AUDIO
            }
        }
        
        response = requests.post(url, headers=headers, json=request_body, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        operation_name = result.get("name")
        
        if operation_name:
            print(f"✅ Video generation started")
            print(f"   Operation: {operation_name.split('/')[-1][:20]}...")
            return operation_name
        else:
            print(f"❌ No operation name in response")
            return None
            
    except Exception as e:
        print(f"❌ Error starting video generation: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def poll_operation_status(operation_name: str) -> Optional[Dict]:
    """
    Poll the status of a video generation operation until complete.
    
    Args:
        operation_name: Full operation name from start_video_generation
    
    Returns:
        Operation result if successful, None otherwise
    """
    try:
        access_token = get_access_token()
        
        url = f"{config.VEO_API_ENDPOINT}/projects/{config.GCP_PROJECT_ID}/locations/{config.VEO_LOCATION}/{config.VEO_MODEL_ID}:fetchPredictOperation"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        request_body = {
            "operationName": operation_name
        }
        
        start_time = time.time()
        max_wait = config.OPERATION_MAX_WAIT_TIME
        poll_interval = config.OPERATION_POLL_INTERVAL
        
        while True:
            elapsed = time.time() - start_time
            
            if elapsed > max_wait:
                print(f"⚠️  Operation timeout after {max_wait}s")
                return None
            
            response = requests.post(url, headers=headers, json=request_body, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("done"):
                print(f"✅ Operation completed in {elapsed:.1f}s")
                return result
            
            # Still running, wait and retry
            print(f"   ⏳ Still processing... ({elapsed:.0f}s elapsed)")
            time.sleep(poll_interval)
            
    except Exception as e:
        print(f"❌ Error polling operation status: {e}")
        return None


def generate_video_from_artwork(artwork: Dict, mongo_client: MongoClient) -> Optional[str]:
    """
    Generate a video using the Veo model from an artwork.
    
    Args:
        artwork: Artwork document from MongoDB
        mongo_client: MongoDB client for marking skipped artworks
    
    Returns:
        GCS URI of the generated video, or None if generation failed
    """
    artwork_id = str(artwork.get("_id"))
    title = artwork.get("title", "Untitled")
    artist = artwork.get("artistName", "Unknown Artist")
    
    # Handle image URL fallback - check imageUrl first, then media array
    image_url = artwork.get("imageUrl")
    if not image_url:
        media = artwork.get("media", [])
        if isinstance(media, list) and len(media) > 0:
            first_item = media[0]
            if isinstance(first_item, dict) and "url" in first_item:
                image_url = first_item["url"]
    
    if not image_url:
        print(f"❌ Artwork {artwork_id} has no valid image URL. Skipping.")
        mark_artwork_as_skipped(mongo_client, artwork_id, "no_image")
        return None
    
    print(f"\n{'='*60}")
    print(f"🎨 Processing: '{title}' by {artist}")
    print(f"   ID: {artwork_id}")
    print(f"   Image: {image_url}")
    print(f"{'='*60}")
    
    try:
        # Download the artwork image
        print(f"📥 Downloading image...")
        image_base64, mime_type = download_image_as_base64(image_url)
        
        # Create the prompt for video generation
        prompt = (
            f"Bring this artwork to life with subtle, artistic motion. "
            f"The piece titled '{title}' by {artist} should maintain its original beauty "
            f"while incorporating elegant, natural movement inspired by brushstrokes or textures. "
            f"Make the animation loop seamlessly, and keep it cinematic."
        )
        
        print(f"📝 Prompt: {prompt[:100]}...")
        print(f"⏱️  Generating video (this may take 2-5 minutes)...")
        
        # Output URI for the video
        output_uri = f"gs://{config.GCS_VIDEO_BUCKET}/videos/"
        
        # Retry logic for transient failures
        operation_name = None
        for attempt in range(2):
            try:
                print(f"   Attempt {attempt + 1}/2...")
                
                # Start video generation
                operation_name = start_video_generation(prompt, image_base64, mime_type, output_uri)
                
                if operation_name:
                    break  # Success, exit retry loop
                else:
                    raise Exception("Failed to start video generation")
                    
            except Exception as e:
                print(f"⚠️  Attempt {attempt + 1} failed: {e}")
                if attempt == 1:  # Last attempt
                    return None
                print("⏳ Retrying in 5 seconds...")
                time.sleep(5)
        
        if not operation_name:
            return None
        
        # Poll until operation completes
        result = poll_operation_status(operation_name)
        
        if not result:
            return None
        
        # Extract GCS URI from response
        response = result.get("response", {})
        videos = response.get("videos", [])
        
        if videos and len(videos) > 0:
            gcs_uri = videos[0].get("gcsUri")
            
            if gcs_uri:
                print(f"✅ Video generated successfully")
                print(f"   GCS URI: {gcs_uri}")
                return gcs_uri
        
        print(f"❌ No video URI in response")
        return None
            
    except Exception as e:
        print(f"❌ Error generating video for artwork {artwork_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_video_url(mongo_client: MongoClient, artwork_id: str, gcs_uri: str) -> bool:
    """
    Save the generated video GCS URI back to MongoDB with metadata.
    
    Args:
        mongo_client: Connected MongoDB client
        artwork_id: ID of the artwork document
        gcs_uri: GCS URI of the generated video
    
    Returns:
        True if successful, False otherwise
    """
    db = mongo_client[config.MONGODB_DATABASE]
    collection = db["artworks"]
    
    try:
        result = collection.update_one(
            {"_id": ObjectId(artwork_id)},
            {"$set": {
                "generatedVideoUrl": gcs_uri,
                "videoGeneratedAt": datetime.utcnow(),
                "videoDuration": config.VIDEO_DURATION_SECONDS,
                "videoResolution": config.VIDEO_RESOLUTION,
                "videoGenerationStatus": "success"
            }}
        )
        
        if result.modified_count > 0:
            print(f"✅ Saved video URL to MongoDB for artwork {artwork_id}")
            return True
        else:
            print(f"⚠️  No document updated for artwork {artwork_id}")
            return False
            
    except Exception as e:
        print(f"❌ Error saving video URL to MongoDB: {e}")
        return False