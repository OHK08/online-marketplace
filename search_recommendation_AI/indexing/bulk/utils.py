import json
import logging
import time # Added for potential retries
from typing import List, Dict, Any, Optional, Tuple # Added Tuple
from pymongo import MongoClient
from google.cloud import aiplatform, storage, secretmanager # Added secretmanager
# Uses the GA library path now
from vertexai.vision_models import MultiModalEmbeddingModel, Image
import vertexai
import requests

# Configure logging (moved configuration to main.py, just get logger here)
logger = logging.getLogger(__name__)

# --- Configuration Loading (Moved to config.py, but keep Secret Manager access here) ---
def get_secret(project_id: str, secret_id: str, version_id: str = "latest") -> str:
    """Fetches a secret value from Google Cloud Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to access secret {secret_id}: {e}", exc_info=True)
        raise

# --- MongoDB Client ---
class MongoDBClient:
    """MongoDB client wrapper."""

    def __init__(self, connection_uri: str, database_name: str, collection_name: str):
        try:
            self.client = MongoClient(connection_uri)
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
            self.db = self.client[database_name]
            self.collection = self.db[collection_name]
            logger.info(f"Connected to MongoDB: {database_name}.{collection_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}", exc_info=True)
            raise

    def fetch_artworks_paginated(self, batch_size: int, limit: Optional[int] = None):
        """
        Fetch artworks from MongoDB using cursor pagination.
        """
        query = {}
        processed_count = 0
        try:
            cursor = self.collection.find(query).batch_size(batch_size)

            if limit:
                cursor = cursor.limit(limit)
                logger.info(f"Applying limit: Fetching max {limit} artworks.")

            batch = []
            for doc in cursor:
                # Ensure _id is serializable if needed later, though not strictly required for embedding input
                doc['_id'] = str(doc['_id'])
                if 'artistId' in doc: # Ensure artistId is also string if it's ObjectId
                    doc['artistId'] = str(doc['artistId'])

                batch.append(doc)
                processed_count += 1
                if len(batch) >= batch_size:
                    yield batch
                    batch = []

                # Respect limit across batches
                if limit and processed_count >= limit:
                    if batch: # Yield any remaining items in the last partial batch
                         yield batch
                    logger.info(f"Reached specified limit of {limit} artworks.")
                    break

            # Yield remaining documents if loop finished naturally and limit not hit exactly
            if batch and (not limit or processed_count < limit):
                yield batch

        except Exception as e:
            logger.error(f"Error fetching artworks from MongoDB: {e}", exc_info=True)
            raise
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()


    def get_total_count(self, limit: Optional[int] = None) -> int:
        """Get total count of artworks, respecting the limit if in test mode."""
        try:
            total_docs = self.collection.count_documents({})
            if limit:
                return min(total_docs, limit)
            return total_docs
        except Exception as e:
            logger.error(f"Error getting total count from MongoDB: {e}", exc_info=True)
            raise

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


# --- Vertex AI Embedder ---
class VertexAIEmbedder:
    """Vertex AI Multimodal Embedding client."""

    def __init__(self, project_id: str, location: str, model_name: str):
        try:
            vertexai.init(project=project_id, location=location)
            # Ensure model name from config is used if needed, though hardcoded below
            self.model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
            self.project_id = project_id
            self.location = location
            logger.info(f"Initialized Vertex AI Embedder: multimodalembedding@001")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI SDK or load model: {e}", exc_info=True)
            raise

    def embed_artworks_batch(self, artworks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int, int]:
        """
        Generate embeddings for a batch of artworks, handling errors individually.
        Returns a tuple: (list_of_successful_results, count_skipped_no_artist, count_text_only)
        """
        results = []
        skipped_no_artist_count = 0
        text_only_count = 0

        for artwork in artworks:
            artwork_id_str = str(artwork.get('_id', 'UNKNOWN_ID')) # Use string ID

            # 1. Check for required artistName field BEFORE API call
            if 'artistName' not in artwork or not artwork['artistName']:
                logger.error(f"SKIP: Artwork {artwork_id_str} missing 'artistName'.")
                skipped_no_artist_count += 1
                continue # Skip this artwork entirely

            try:
                # 2. Construct text input
                text_parts = [
                    artwork.get('title', ''),
                    artwork.get('description', ''),
                    ' '.join(artwork.get('tags', [])),
                    artwork.get('artistName', '') # Already checked it exists
                ]
                text_input = ' '.join(filter(None, text_parts)).strip()
                if not text_input:
                    logger.warning(f"WARNING: Artwork {artwork_id_str} has empty combined text.")
                    # Decide if you want to skip or proceed with image-only if available

                # 3. Get image URL and attempt to load image
                image_url = None
                image_input = None
                is_text_only = False
                media_list = artwork.get('media')

                if media_list and isinstance(media_list, list) and len(media_list) > 0:
                    first_media = media_list[0]
                    if isinstance(first_media, dict):
                         image_url = first_media.get('url')

                if image_url:
                    try:
                        if image_url.startswith('http://') or image_url.startswith('https://'):
                            response = requests.get(image_url, timeout=10) # Added timeout
                            response.raise_for_status()
                            image_bytes = response.content
                            image_input = Image(image_bytes)
                        elif image_url.startswith('gs://'):
                             image_input = Image.load_from_file(image_url)
                        else:
                             # Assume local path or other URI scheme if needed, handle appropriately
                             # For Cloud Run, only gs:// or http(s):// are practical
                             logger.warning(f"WARNING: Artwork {artwork_id_str} has unsupported image URL scheme: {image_url}. Using text-only.")
                             is_text_only = True
                    except requests.exceptions.RequestException as req_err:
                         logger.warning(f"WARNING: Artwork {artwork_id_str} failed to download image URL {image_url} ({req_err}). Using text-only.")
                         is_text_only = True
                    except Exception as img_load_err:
                         logger.warning(f"WARNING: Artwork {artwork_id_str} failed to load image from {image_url} ({img_load_err}). Using text-only.")
                         is_text_only = True
                else:
                    logger.warning(f"WARNING: Artwork {artwork_id_str} has no media URL. Using text-only.")
                    is_text_only = True

                # 4. Call Embedding API
                embeddings_response = None
                try:
                    if not is_text_only and image_input:
                        embeddings_response = self.model.get_embeddings(
                            image=image_input,
                            contextual_text=text_input,
                            dimension=1408 # Explicitly set dimension
                        )
                    else:
                        embeddings_response = self.model.get_embeddings(
                            contextual_text=text_input,
                            dimension=1408 # Explicitly set dimension
                        )
                        if is_text_only:
                            text_only_count += 1 # Increment only if intentionally text-only

                except Exception as embed_err:
                     logger.error(f"ERROR: Vertex AI API call failed for artwork {artwork_id_str}: {embed_err}")
                     continue # Skip this artwork on API error

                # 5. Extract vector and check validity
                embedding_vector = None
                if embeddings_response:
                    # The response structure might differ slightly based on input (image vs text)
                    if hasattr(embeddings_response, 'image_embedding') and embeddings_response.image_embedding:
                        embedding_vector = embeddings_response.image_embedding
                    elif hasattr(embeddings_response, 'text_embedding') and embeddings_response.text_embedding:
                         embedding_vector = embeddings_response.text_embedding

                # Check if embedding_vector is a valid list of floats/ints
                if isinstance(embedding_vector, list) and all(isinstance(val, (float, int)) for val in embedding_vector):
                     if len(embedding_vector) == 1408:
                          results.append({
                              'artwork_id': artwork_id_str,
                              'embedding': embedding_vector,
                              'artwork': artwork, # Pass original doc for formatter
                              'is_text_only': is_text_only
                          })
                     else:
                          logger.error(f"ERROR: Artwork {artwork_id_str} embedding has incorrect dimension: {len(embedding_vector)}. Skipping.")
                          continue # Skip if dimensions mismatch
                else:
                    # This handles the case where embedding_vector might be None or invalid type
                    logger.error(f"ERROR: Artwork {artwork_id_str} produced invalid or null embedding. Skipping.")
                    continue # Skip this artwork


            except Exception as e:
                # Catch-all for unexpected errors during processing of a single artwork
                logger.error(f"ERROR: Unexpected error processing artwork {artwork_id_str}: {e}", exc_info=True)
                continue # Skip this artwork

        return results, skipped_no_artist_count, text_only_count


# --- JSONL Formatter ---
class JSONLFormatter:
    """Format embedding results as JSONL for Vertex AI Vector Search."""

    @staticmethod
    def format_artwork_embedding(artwork_id: str, embedding: List[float], artwork: Dict[str, Any]) -> Optional[str]:
        """
        Format a single artwork embedding as a JSONL line string.
        Returns None if essential data is missing or formatting fails.
        """
        try:
            # Basic validation
            if not artwork_id or not isinstance(embedding, list) or len(embedding) != 1408:
                 logger.error(f"Invalid input for formatting artwork {artwork_id}. Embedding invalid.")
                 return None

            # Prepare token restricts
            restricts_dict = {} # Use dict to ensure unique namespaces

            # artistId (token)
            if artwork.get('artistId'):
                 # Ensure artistId is a string
                 restricts_dict["artistId"] = {"namespace": "artistId", "allow": [str(artwork['artistId'])]}

            # tags (token array) - *** FIX APPLIED HERE ***
            tags = artwork.get('tags')
            if tags and isinstance(tags, list) and len(tags) > 0:
                 # Filter out any non-string tags just in case
                 valid_tags = [str(tag) for tag in tags if isinstance(tag, str) and tag]
                 if valid_tags:
                      restricts_dict["tags"] = {"namespace": "tags", "allow": valid_tags} # Single entry

            # status (token)
            if artwork.get('status'):
                 restricts_dict["status"] = {"namespace": "status", "allow": [str(artwork['status'])]}

            # Convert dict back to list for final JSON
            restricts = list(restricts_dict.values())

            # Prepare numeric restricts
            numeric_restricts = []

            # price (int)
            price = artwork.get('price')
            if price is not None:
                 try:
                      numeric_restricts.append({
                          "namespace": "price",
                          "value_int": int(price)
                      })
                 except (ValueError, TypeError):
                     logger.warning(f"Artwork {artwork_id}: Could not convert price '{price}' to int for numeric restrict.")

            # likeCount (int)
            like_count = artwork.get('likeCount')
            if like_count is not None:
                  try:
                      numeric_restricts.append({
                          "namespace": "likeCount",
                          "value_int": int(like_count)
                      })
                  except (ValueError, TypeError):
                     logger.warning(f"Artwork {artwork_id}: Could not convert likeCount '{like_count}' to int.")

            # purchaseCount (int)
            purchase_count = artwork.get('purchaseCount')
            if purchase_count is not None:
                  try:
                      numeric_restricts.append({
                          "namespace": "purchaseCount",
                          "value_int": int(purchase_count)
                      })
                  except (ValueError, TypeError):
                     logger.warning(f"Artwork {artwork_id}: Could not convert purchaseCount '{purchase_count}' to int.")

            # Construct JSONL object
            jsonl_object = {
                "id": artwork_id,
                "embedding": embedding,
                # Only include restricts/numeric_restricts if they are not empty
                **({"restricts": restricts} if restricts else {}),
                **({"numeric_restricts": numeric_restricts} if numeric_restricts else {})
            }

            return json.dumps(jsonl_object)

        except Exception as e:
            logger.error(f"ERROR: Failed to format JSONL for artwork {artwork_id}: {e}", exc_info=True)
            return None


# --- GCS Uploader ---
class GCSUploader:
    """Google Cloud Storage uploader."""

    def __init__(self, bucket_name: str):
        try:
            self.client = storage.Client()
            self.bucket = self.client.bucket(bucket_name)
            # Check if bucket exists and client has permissions (optional but good)
            # self.bucket.reload()
            self.bucket_name = bucket_name
            logger.info(f"Initialized GCS uploader for bucket: {bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client for bucket {bucket_name}: {e}", exc_info=True)
            raise

    def upload_file(self, local_file_path: str, gcs_path: str):
        """
        Upload a local file to GCS.
        """
        try:
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_filename(local_file_path)
            full_path = f"gs://{self.bucket_name}/{gcs_path}"
            logger.info(f"Successfully uploaded file to {full_path}")
            return full_path
        except Exception as e:
            logger.error(f"Failed to upload {local_file_path} to GCS path {gcs_path}: {e}", exc_info=True)
            raise
