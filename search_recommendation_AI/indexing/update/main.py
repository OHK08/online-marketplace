# ============================================================================
# FILE: indexing/update/main.py
# ============================================================================
import os
import sys
import logging
from datetime import datetime, timedelta, timezone # <-- Added timezone here
from config import Config
from typing import List, Dict # <-- Added import for List, Dict
from utils import (
    MongoDBClient, 
    VertexAIEmbedder, 
    JSONLFormatter, 
    GCSUploader,
    VertexAIIndexUpdater
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DailyUpdateJob:
    """Daily incremental update job for Vertex AI Index.""" # <-- Updated description
    
    def __init__(self, config: Config):
        self.config = config
        self.stats = {
            'found': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped_no_artist': 0,
            'text_only_embeddings': 0
        }
        # --- FIXED DEPRECATION WARNING ---
        self.run_timestamp = datetime.now(timezone.utc)
    
    def run(self):
        """Execute the daily update job."""
        logger.info("=" * 80)
        logger.info("Starting Daily Update Job")
        logger.info(f"Run timestamp: {self.run_timestamp}")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        gcs_output_uri = None # Variable to store the final GCS path for summary
        
        try:
            # Validate configuration
            self.config.validate()
            logger.info(f"Configuration validated. Test mode: {self.config.test_mode}")
            
            # Initialize clients
            logger.info("Initializing clients...")
            mongodb_uri = self.config.get_mongodb_uri()
            mongo_client = MongoDBClient(
                mongodb_uri,
                self.config.mongodb_database,
                self.config.mongodb_collection
            )
            
            embedder = VertexAIEmbedder(
                self.config.gcp_project_id,
                self.config.vertex_ai_location,
                self.config.embedding_model
            )
            
            gcs_uploader = GCSUploader(self.config.gcs_bucket_name)
            
            index_updater = VertexAIIndexUpdater(
                self.config.gcp_project_id,
                self.config.vertex_ai_location,
                self.config.vertex_ai_index_id
            )
            
            # Fetch recently updated artworks
            logger.info(f"Fetching artworks updated in the last {self.config.update_window_hours} hours...")

            limit = self.config.test_limit if self.config.test_mode else None

            updated_artworks = mongo_client.fetch_recently_updated_artworks(
                0,
                limit
            )

            
            self.stats['found'] = len(updated_artworks)
            
            if self.stats['found'] == 0:
                logger.info("No recently updated artworks found. Exiting.")
                mongo_client.close()
                self._print_summary(0) # Pass 0 duration
                sys.exit(0)
            
            # Generate dated folder path
            date_folder = self.run_timestamp.strftime("%Y-%m-%d")
            gcs_folder_path = f"{self.config.gcs_updates_base_path}/{date_folder}"
            
            # Generate unique filename with timestamp
            timestamp_str = self.run_timestamp.strftime("%Y%m%d-%H%M%S")
            # --- FIXED FILENAME EXTENSION ---
            json_filename = f"update-{timestamp_str}.json" 
            local_json_path = os.path.join(self.config.local_jsonl_dir, json_filename) # Use config's local dir
            gcs_file_path_relative = f"{gcs_folder_path}/{json_filename}" # Relative path for upload
            
            # Ensure local temp directory exists (added for robustness)
            os.makedirs(self.config.local_jsonl_dir, exist_ok=True)

            # Process artworks
            logger.info("Processing updated artworks...")
            self._process_artworks(updated_artworks, embedder, local_json_path)
            
            # Check if any successful embeddings
            if self.stats['successful'] == 0:
                logger.warning("No artworks were successfully embedded. Skipping upload and index update.")
                mongo_client.close()
                if os.path.exists(local_json_path):
                    os.remove(local_json_path)
                self._print_summary((datetime.now() - start_time).total_seconds())
                sys.exit(1) # Exit with error code if nothing was processed
            
            # Upload to GCS
            logger.info(f"Uploading update JSON to GCS: {gcs_file_path_relative}")
            # --- Store full GCS URI ---
            gcs_output_uri = gcs_uploader.upload_file(local_json_path, gcs_file_path_relative) 
            
            # --- FIXED THIS BLOCK ---
            # Update Vertex AI Index (point to the specific GCS file)
            logger.info(f"Updating Vertex AI Index with file: {gcs_output_uri}")
            index_updater.update_index(gcs_output_uri) # Pass the full gs:// path
            # --- END OF FIX ---
            
            # Clean up local file
            if os.path.exists(local_json_path):
                os.remove(local_json_path)
                logger.info("Cleaned up local temporary file")

            # Close DB connection
            mongo_client.close()
            
            # Print summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            self._print_summary(duration, gcs_output_uri) # Pass file URI to summary
            
            # Exit with appropriate code
            if self.stats['failed'] > 0:
                logger.warning("Job completed with some failures")
                sys.exit(1)
            else:
                logger.info("Job completed successfully!")
                sys.exit(0)
            
        except Exception as e:
            logger.error(f"Fatal error in daily update job: {e}", exc_info=True)
            # Ensure DB connection is closed on error
            if 'mongo_client' in locals() and mongo_client:
                 try:
                     mongo_client.close()
                 except Exception: # Ignore errors during close on exception path
                     pass
            # Clean up local file on error if it exists
            if 'local_json_path' in locals() and os.path.exists(local_json_path):
                 try:
                     os.remove(local_json_path)
                     logger.info("Cleaned up local temporary file after error")
                 except Exception:
                     pass
            sys.exit(1) # Exit with error code
    
    def _process_artworks(
        self, 
        artworks: List[Dict], 
        embedder: VertexAIEmbedder, 
        output_path: str
    ):
        """Process artworks: embed, format, write to JSON.""" # <-- Updated description
        self.stats['processed'] = len(artworks)
        
        # Open JSON file for writing
        with open(output_path, 'w') as json_file:
            # Process in batches
            for i in range(0, len(artworks), self.config.embedding_batch_size):
                batch = artworks[i:i + self.config.embedding_batch_size]
                
                logger.info(f"Processing batch {i//self.config.embedding_batch_size + 1}: {len(batch)} artworks")
                
                # Generate embeddings
                embedding_results = embedder.embed_artworks_batch(batch)
                
                # Format and write to JSON file
                for result in embedding_results:
                    # --- FIXED FILENAME EXTENSION ---
                    json_line = JSONLFormatter.format_artwork_embedding( 
                        result['artwork_id'],
                        result['embedding'],
                        result['artwork']
                    )
                    json_file.write(json_line + '\n') # Still write line-by-line
                    self.stats['successful'] += 1
                    
                    if result.get('is_text_only', False):
                        self.stats['text_only_embeddings'] += 1
                
                # Calculate failures in this batch
                batch_failed = len(batch) - len(embedding_results)
                self.stats['failed'] += batch_failed
        
        logger.info(f"Completed processing: {self.stats['successful']} successful, {self.stats['failed']} failed")
    
    # --- UPDATED PARAMETER NAME ---
    def _print_summary(self, duration: float, gcs_file_uri: str = None):
        """Print job execution summary."""
        logger.info("=" * 80)
        logger.info("DAILY UPDATE JOB SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Run timestamp: {self.run_timestamp}")
        logger.info(f"Update window: {self.config.update_window_hours} hours")
        logger.info(f"Recently updated artworks found: {self.stats['found']}")
        logger.info(f"Artworks processed: {self.stats['processed']}")
        logger.info(f"Successfully embedded: {self.stats['successful']}")
        logger.info(f"Failed to embed: {self.stats['failed']}")
        logger.info(f"Skipped (no artistName): {self.stats['skipped_no_artist']}")
        logger.info(f"Text-only embeddings: {self.stats['text_only_embeddings']}")
        logger.info(f"Execution time: {duration:.2f} seconds")
        if gcs_file_uri:
            # --- UPDATED LOG MESSAGE ---
            logger.info(f"Index update file: {gcs_file_uri}") 
        logger.info("=" * 80)


def main():
    """Main entry point."""
    # Load configuration
    config = Config()
    
    # Create and run job
    job = DailyUpdateJob(config)
    job.run()


if __name__ == "__main__":
    main()