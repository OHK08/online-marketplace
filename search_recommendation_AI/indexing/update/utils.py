# ============================================================================
# FILE: indexing/update/utils.py
# ============================================================================
import json
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
from google.cloud import aiplatform, storage
# --- ADDED THIS IMPORT ---
from google.cloud.aiplatform_v1.types import IndexDatapoint
from vertexai.preview.vision_models import MultiModalEmbeddingModel, Image
import vertexai
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client wrapper for update operations."""
    
    def __init__(self, connection_uri: str, database_name: str, collection_name: str):
        self.client = MongoClient(connection_uri)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        logger.info(f"Connected to MongoDB: {database_name}.{collection_name}")
    
#
# This goes in indexing/utils.py
#
    def fetch_recently_updated_artworks(self, hours: int, limit: int = None):
        """
        Fetch artworks updated recently.
        If hours is 0, fetch ALL artworks (backfill mode).
        """
        if hours == 0:
            # === BACKFILL MODE ===
            # Set timestamp to 0 to get all documents
            timestamp_ms = 0
            logger.info("Querying ALL artworks (backfill mode, timestamp 0)")
        else:
            # === NORMAL DAILY MODE ===
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            timestamp_ms = int(cutoff_time.timestamp() * 1000)
            logger.info(f"Querying artworks updated since: {cutoff_time} (timestamp: {timestamp_ms})")
        
        query = {
            "updatedAt_timestamp": {"$gte": timestamp_ms}
        }
        
        try:
            if limit:
                artworks = list(self.collection.find(query).limit(limit))
            else:
                artworks = list(self.collection.find(query))
            
            logger.info(f"Found {len(artworks)} recently updated artworks")
            return artworks
        except Exception as e:
            logger.error(f"Failed to fetch artworks from MongoDB: {e}")
            return []
    
    def close(self):
        """Close MongoDB connection."""
        self.client.close()
        logger.info("MongoDB connection closed")


class VertexAIEmbedder:
    """Vertex AI Multimodal Embedding client."""
    
    def __init__(self, project_id: str, location: str, model_name: str):
        vertexai.init(project=project_id, location=location)
        self.model = MultiModalEmbeddingModel.from_pretrained(model_name)
        self.project_id = project_id
        self.location = location
        logger.info(f"Initialized Vertex AI Embedder: {model_name}")
    
    def embed_artworks_batch(self, artworks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a batch of artworks.
        
        Args:
            artworks: List of artwork documents
        
        Returns:
            List of dicts with artwork_id, embedding, and metadata
        """
        results = []
        

        for artwork in artworks:
            
            try:
                artwork_id = str(artwork['_id'])
                
                # Check for required artistName field
                if 'artistName' not in artwork or not artwork['artistName']:
                    logger.error(f"SKIP: Artwork {artwork_id} missing artistName field")
                    continue
                
                # Construct text input
                text_parts = [
                    artwork.get('title', ''),
                    artwork.get('description', ''),
                    ' '.join(artwork.get('tags', [])),
                    artwork.get('artistName', '')
                ]
                text_input = ' '.join(filter(None, text_parts))
                
                # Get image URL
                image_url = None
                if artwork.get('media') and len(artwork['media']) > 0:
                    image_url = artwork['media'][0].get('url')
                
                is_text_only = False  # Flag for stats
                
                # Generate embedding
                if image_url:
                    try:
                        # Multimodal: text + image
                        if image_url.startswith('http://') or image_url.startswith('https://'):
                            # Download image from web URL
                            response = requests.get(image_url, timeout=30)
                            response.raise_for_status()
                            image_bytes = response.content
                            image = Image(image_bytes)
                        else:
                            # Assume it's a GCS URI or local file
                            image = Image.load_from_file(image_url)
                        
                        embeddings = self.model.get_embeddings(
                            image=image,
                            contextual_text=text_input
                        )
                    except Exception as img_error:
                        # If image loading fails, fall back to text-only
                        logger.warning(f"WARNING: Artwork {artwork_id} failed to load image ({img_error}), using text-only embedding")
                        is_text_only = True
                        embeddings = self.model.get_embeddings(
                            contextual_text=text_input
                        )
                else:
                    # Text-only fallback
                    logger.warning(f"WARNING: Artwork {artwork_id} missing image, using text-only embedding")
                    is_text_only = True
                    embeddings = self.model.get_embeddings(
                        contextual_text=text_input
                    )
                
                # Extract embedding vector
                embedding_vector = embeddings.image_embedding if hasattr(embeddings, 'image_embedding') else embeddings.text_embedding
                
                # Validate embedding is not None
                if embedding_vector is None:
                    logger.error(f"ERROR: Artwork {artwork_id} embedding is None, skipping")
                    continue
                
                results.append({
                    'artwork_id': artwork_id,
                    'embedding': embedding_vector,
                    'artwork': artwork,
                    'is_text_only': is_text_only
                })
                
            except Exception as e:
                logger.error(f"ERROR: Failed to embed artwork {artwork.get('_id')}: {e}")
                continue
        
        return results


class JSONLFormatter:
    """Format embedding results as JSONL for Vertex AI Vector Search."""
    
    @staticmethod
    def format_artwork_embedding(artwork_id: str, embedding: List[float], artwork: Dict[str, Any]) -> str:
        """
        Format a single artwork embedding as a JSONL line.

        Args:
            artwork_id: Unique artwork identifier
            embedding: Embedding vector (list of floats)
            artwork: Original artwork document

        Returns:
            JSON string line
        """
        # Prepare token restricts
        restricts = []

        # artistId (token)
        if 'artistId' in artwork and artwork['artistId']: # Added check for non-empty
            restricts.append({
                "namespace": "artistId",
                "allow_list": [str(artwork['artistId'])] # <-- FIELD NAME CHANGED
            })

        # tags (token array)
        if 'tags' in artwork and artwork['tags']:
            # Filter out empty or None tags before creating restrictions
            valid_tags = [tag for tag in artwork['tags'] if tag] 
            if valid_tags: # Only add if there are valid tags
                restricts.append({
                    "namespace": "tags",
                    "allow_list": valid_tags # <-- FIELD NAME CHANGED & USE FILTERED LIST
                })

        # status (token)
        if 'status' in artwork and artwork['status']: # Added check for non-empty
            restricts.append({
                "namespace": "status",
                "allow_list": [artwork['status']] # <-- FIELD NAME CHANGED
            })

        # Prepare numeric restricts
        numeric_restricts = []

        # price (int) - Check if price is not None before converting
        if 'price' in artwork and artwork['price'] is not None:
            try:
                numeric_restricts.append({
                    "namespace": "price",
                    "value_int": int(artwork['price']) # Ensure it's an int
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Artwork {artwork_id}: Could not convert price '{artwork['price']}' to int. Skipping price restrict. Error: {e}")

        # likeCount (int) - Check if not None
        if 'likeCount' in artwork and artwork['likeCount'] is not None:
            try:
                numeric_restricts.append({
                    "namespace": "likeCount",
                    "value_int": int(artwork['likeCount'])
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Artwork {artwork_id}: Could not convert likeCount '{artwork['likeCount']}' to int. Skipping likeCount restrict. Error: {e}")

        # purchaseCount (int) - Check if not None
        if 'purchaseCount' in artwork and artwork['purchaseCount'] is not None:
            try:
                numeric_restricts.append({
                    "namespace": "purchaseCount",
                    "value_int": int(artwork['purchaseCount'])
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Artwork {artwork_id}: Could not convert purchaseCount '{artwork['purchaseCount']}' to int. Skipping purchaseCount restrict. Error: {e}")

        # Construct JSONL object
        jsonl_object = {
            "id": artwork_id,
            "embedding": embedding,
            # Only include restricts/numeric_restricts if they are not empty
            **({"restricts": restricts} if restricts else {}),
            **({"numeric_restricts": numeric_restricts} if numeric_restricts else {})
        }

        return json.dumps(jsonl_object)


class GCSUploader:
    """Google Cloud Storage uploader."""
    
    def __init__(self, bucket_name: str):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.bucket_name = bucket_name
        logger.info(f"Initialized GCS uploader for bucket: {bucket_name}")
    
    def upload_file(self, local_file_path: str, gcs_path: str) -> str:
        """
        Upload a local file to GCS.
        
        Args:
            local_file_path: Path to local file
            gcs_path: Destination path in GCS (without gs:// prefix)
        
        Returns:
            Full GCS URI (gs://bucket/path)
        """
        try:
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_filename(local_file_path)
            full_path = f"gs://{self.bucket_name}/{gcs_path}"
            logger.info(f"Successfully uploaded file to {full_path}")
            return full_path
        except Exception as e:
            logger.error(f"Failed to upload file to GCS: {e}")
            raise


class VertexAIIndexUpdater:
    """Handles Vertex AI Index update operations."""
    
    def __init__(self, project_id: str, location: str, index_id: str):
        aiplatform.init(project=project_id, location=location)
        self.project_id = project_id
        self.location = location
        self.index_id = index_id
        logger.info(f"Initialized Vertex AI Index Updater for index: {index_id}")
    
    # --- REPLACED THIS ENTIRE METHOD ---
    def update_index(self, gcs_file_path: str):
        """
        Updates a STREAM_UPDATE index using upsert_datapoints.
        Reads the JSONL file from GCS and streams the updates.
        """
        logger.info(f"Fetching index: {self.index_id}")
        index = aiplatform.MatchingEngineIndex(index_name=self.index_id)

        logger.info(f"Reading update file from GCS: {gcs_file_path}")
        
        # 1. Parse GCS path
        if not gcs_file_path.startswith("gs://"):
            raise ValueError(f"Invalid GCS path: {gcs_file_path}")
        
        bucket_name, blob_name = gcs_file_path.replace("gs://", "").split("/", 1)
        
        # 2. Download file from GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        try:
            file_content = blob.download_as_text()
        except Exception as e:
            logger.error(f"Failed to download GCS file {gcs_file_path}: {e}")
            raise

        # 3. Parse JSONL and create datapoints
        datapoints = []
        for line in file_content.strip().split('\n'):
            if not line:
                continue
            try:
                record = json.loads(line)
                
                # Create the datapoint object
                datapoint = IndexDatapoint(
                    datapoint_id=record["id"],
                    feature_vector=record["embedding"],
                    restricts=record.get("restricts", []),
                    numeric_restricts=record.get("numeric_restricts", [])
                )
                datapoints.append(datapoint)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Skipping malformed line in {gcs_file_path}: {e}")
                
        if not datapoints:
            logger.info("No valid datapoints found in file. No index update needed.")
            return

        # 4. Call upsert_datapoints
        logger.info(f"Upserting {len(datapoints)} datapoints to index {self.index_id}...")
        try:
            # Note: upsert_datapoints returns None on success
            index.upsert_datapoints(datapoints=datapoints)
            logger.info("✅ Successfully upserted datapoints to Vertex AI Index.")
        except Exception as e:
            logger.error(f"Failed to upsert datapoints to Vertex AI index: {e}")
            raise