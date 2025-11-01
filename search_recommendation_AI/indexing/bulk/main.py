# ============================================================================
# FILE: indexing/bulk/main.py
# ============================================================================
import os
import sys
import logging
from datetime import datetime
from config import Config
# Ensure utils.py contains the classes/functions as defined in the updated version
from utils import MongoDBClient, VertexAIEmbedder, JSONLFormatter, GCSUploader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BulkIndexingJob:
    """Main bulk indexing job orchestrator."""

    def __init__(self, config: Config):
        self.config = config
        self.stats = {
            'total_artworks': 0,
            'processed': 0, # Total items pulled from DB batch for processing attempt
            'successful': 0, # Successfully embedded AND formatted
            'failed': 0, # Failed during embedding API call OR formatting
            'skipped_no_artist': 0, # Skipped due to missing artistName
            'text_only_embeddings': 0 # Successfully embedded but used text-only fallback
        }

    def run(self):
        """Execute the bulk indexing job."""
        logger.info("=" * 80)
        logger.info("Starting Bulk Indexing Job")
        logger.info("=" * 80)

        start_time = datetime.now()
        mongo_client = None # Initialize to None for cleanup

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

            # Get total count
            limit = self.config.test_limit if self.config.test_mode else None
            # Fetch total count respecting limit for accurate progress logging
            self.stats['total_artworks'] = mongo_client.get_total_count(limit)
            logger.info(f"Total artworks to process (respecting limit): {self.stats['total_artworks']}")

            # Process artworks
            logger.info("Starting artwork processing...")
            self._process_artworks(mongo_client, embedder)

            # Upload to GCS only if successful items were generated
            gcs_path = "N/A - No successful items"
            if self.stats['successful'] > 0 and os.path.exists(self.config.local_jsonl_path):
                 logger.info("Uploading JSONL file to GCS...")
                 gcs_path = gcs_uploader.upload_file(
                     self.config.local_jsonl_path,
                     self.config.gcs_output_path
                 )
            elif self.stats['successful'] == 0:
                 logger.warning("No artworks were successfully embedded and formatted. Skipping GCS upload.")


            # Clean up local file regardless
            if os.path.exists(self.config.local_jsonl_path):
                os.remove(self.config.local_jsonl_path)
                logger.info("Cleaned up local temporary file")

            # Print summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            self._print_summary(duration, gcs_path)

            # Calculate total errors/skips for exit code
            total_issues = self.stats['failed'] + self.stats['skipped_no_artist']

            # Exit with appropriate code
            if total_issues > 0:
                logger.warning(f"Job completed with {total_issues} issues (failures + skips).")
                # Decide if skip should cause non-zero exit? For now, only fail counts.
                if self.stats['failed'] > 0:
                     sys.exit(1) # Exit with error if there were actual failures
                else:
                     sys.exit(0) # Exit successfully if only skips occurred
            else:
                logger.info("Job completed successfully!")
                sys.exit(0)

        except Exception as e:
            logger.error(f"Fatal error in bulk indexing job: {e}", exc_info=True)
            sys.exit(1) # Ensure non-zero exit on fatal error
        finally:
             # Ensure MongoDB connection is closed even if errors occur
             if mongo_client:
                  mongo_client.close()


    def _process_artworks(self, mongo_client: MongoDBClient, embedder: VertexAIEmbedder):
        """Process artworks: fetch, embed, format, write to JSONL."""
        limit = self.config.test_limit if self.config.test_mode else None
        processed_in_job = 0 # Track items actually processed in this run

        # Open JSONL file for writing
        # Ensure directory exists if local_jsonl_path includes one
        os.makedirs(os.path.dirname(self.config.local_jsonl_path or '.'), exist_ok=True)
        with open(self.config.local_jsonl_path, 'w') as jsonl_file:
            # Fetch artworks in batches
            for batch in mongo_client.fetch_artworks_paginated(
                self.config.mongodb_batch_size,
                limit
            ):
                batch_start_count = processed_in_job
                processed_in_job += len(batch) # Increment total processed attempt counter

                logger.info(f"Processing DB batch: {len(batch)} artworks (Total processed attempts: {processed_in_job}/{self.stats['total_artworks']})")

                # Process in smaller embedding batches
                for i in range(0, len(batch), self.config.embedding_batch_size):
                    embedding_sub_batch = batch[i:i + self.config.embedding_batch_size]
                    self.stats['processed'] += len(embedding_sub_batch) # Count items sent for embedding attempt

                    # Generate embeddings - Call the corrected function name
                    # It returns results (list of successes), skipped count, text_only count
                    embedding_results, skipped_count, text_only_count = embedder.embed_artworks_batch(embedding_sub_batch)

                    # Update overall stats from the results of this sub-batch
                    self.stats['skipped_no_artist'] += skipped_count
                    self.stats['text_only_embeddings'] += text_only_count

                    # Format and write successful results ONLY
                    sub_batch_formatted_count = 0
                    sub_batch_format_failed_count = 0
                    for result in embedding_results: # This list only contains successfully embedded items
                        jsonl_line = JSONLFormatter.format_artwork_embedding(
                            result['artwork_id'],
                            result['embedding'],
                            result['artwork']
                        )
                        if jsonl_line:
                            jsonl_file.write(jsonl_line + '\n')
                            sub_batch_formatted_count += 1
                        else:
                            # Increment failed count if formatting failed
                            sub_batch_format_failed_count += 1
                            logger.error(f"Failed to format JSONL for successfully embedded artwork ID: {result.get('artwork_id', 'UNKNOWN')}")

                    self.stats['successful'] += sub_batch_formatted_count
                    self.stats['failed'] += sub_batch_format_failed_count # Add formatting failures to overall fail count

                # Log progress after processing a full DB batch
                if processed_in_job % 100 == 0 or processed_in_job == self.stats['total_artworks']:
                     # Use processed_in_job for progress relative to total expected
                    logger.info(f"Progress: {processed_in_job}/{self.stats['total_artworks']} artworks processed (DB read)")

    def _print_summary(self, duration: float, gcs_path: str):
        """Print job execution summary."""
        logger.info("=" * 80)
        logger.info("BULK INDEXING JOB SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total artworks target: {self.stats['total_artworks']}")
        logger.info(f"Artworks processed (embedding attempts): {self.stats['processed']}")
        logger.info(f"Successfully embedded & formatted: {self.stats['successful']}")
        logger.info(f"Failed (embedding API or formatting): {self.stats['failed']}")
        logger.info(f"Skipped (missing artistName): {self.stats['skipped_no_artist']}")
        logger.info(f"Text-only embeddings (successful): {self.stats['text_only_embeddings']}")
        logger.info(f"Execution time: {duration:.2f} seconds")
        logger.info(f"Output file uploaded to: {gcs_path}")
        logger.info("=" * 80)


def main():
    """Main entry point."""
    # Load configuration
    config = Config()

    # Create and run job
    job = BulkIndexingJob(config)
    job.run()


if __name__ == "__main__":
    main()
