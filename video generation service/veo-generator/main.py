# ============================================================================
# FILE: main.py
# ============================================================================
"""
Main entry point for veo-generator Cloud Run Job.
Orchestrates the video generation process for multiple artworks.
"""
import sys
import config
import utils


def main():
    """Main function that orchestrates the video generation process."""
    print("\n" + "="*60)
    print("🎬 VEO VIDEO GENERATOR - STARTING")
    print("="*60 + "\n")
    
    # Validate configuration
    try:
        config.validate_config()
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        sys.exit(1)
    
    # Connect to MongoDB
    try:
        mongo_client = utils.get_mongo_client()
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)
    
    # Fetch artworks to process
    try:
        artworks = utils.fetch_artworks_to_process(mongo_client)
        
        if len(artworks) == 0:
            print("\n✅ No artworks to process. Job complete!")
            mongo_client.close()
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Failed to fetch artworks: {e}")
        mongo_client.close()
        sys.exit(1)
    
    # Process each artwork
    total = len(artworks)
    successful = 0
    failed = 0
    skipped = 0
    
    print(f"\n{'='*60}")
    print(f"📊 PROCESSING {total} ARTWORKS")
    print(f"{'='*60}\n")
    
    for idx, artwork in enumerate(artworks, 1):
        artwork_id = str(artwork.get("_id"))
        title = artwork.get("title", "Untitled")
        
        print(f"\n[{idx}/{total}] Processing artwork: {title}")
        
        try:
            # Generate video (passes mongo_client for marking skipped artworks)
            gcs_uri = utils.generate_video_from_artwork(artwork, mongo_client)
            
            if gcs_uri:
                # Save the video URL to MongoDB
                if utils.save_video_url(mongo_client, artwork_id, gcs_uri):
                    successful += 1
                    print(f"✅ [{idx}/{total}] SUCCESS: {title}")
                else:
                    failed += 1
                    print(f"⚠️  [{idx}/{total}] PARTIAL: Video generated but not saved to DB")
            else:
                # Video was not generated (could be skipped or failed)
                # Check if it was marked as skipped
                db = mongo_client[config.MONGODB_DATABASE]
                artwork_doc = db["artworks"].find_one({"_id": artwork["_id"]})
                if artwork_doc and "skipped" in artwork_doc.get("videoGenerationStatus", ""):
                    skipped += 1
                    print(f"⏭️  [{idx}/{total}] SKIPPED: {title}")
                else:
                    failed += 1
                    print(f"❌ [{idx}/{total}] FAILED: {title}")
                
        except Exception as e:
            failed += 1
            print(f"❌ [{idx}/{total}] ERROR processing {title}: {e}")
            # Continue to next artwork instead of stopping
            continue
    
    # Close MongoDB connection
    mongo_client.close()
    
    # Print final summary
    print(f"\n{'='*60}")
    print(f"🎬 VEO VIDEO GENERATOR - COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Successful: {successful}/{total}")
    print(f"⏭️  Skipped: {skipped}/{total}")
    print(f"❌ Failed: {failed}/{total}")
    print(f"{'='*60}\n")
    
    # Exit with appropriate status code
    if failed > 0:
        print(f"⚠️  Job completed with {failed} failures")
        sys.exit(0)  # Still exit 0 since we want partial success
    else:
        print(f"🎉 All videos generated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()