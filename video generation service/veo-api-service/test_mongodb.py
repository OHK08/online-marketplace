from api.mongo_client import get_mongo_client

# Get MongoDB client
db = get_mongo_client()
artworks = db["artworks"]

# Check total artworks
total_count = artworks.count_documents({})
print(f"Total artworks in collection: {total_count}")

# Check artworks WITH generatedVideoUrl
with_video_count = artworks.count_documents({"generatedVideoUrl": {"$exists": True}})
print(f"Artworks with generatedVideoUrl: {with_video_count}")

# Show a sample artwork with video
sample = artworks.find_one({"generatedVideoUrl": {"$exists": True}})
if sample:
    print(f"\nSample artwork with video:")
    print(f"  _id: {sample['_id']}")
    print(f"  title: {sample.get('title')}")
    print(f"  generatedVideoUrl: {sample.get('generatedVideoUrl')}")
else:
    print("\nNo artworks found with generatedVideoUrl!")
    
# Check if the field exists but might be null/empty
null_video = artworks.find_one({"generatedVideoUrl": {"$exists": True}})
print(f"\nFirst doc with generatedVideoUrl field: {null_video.get('generatedVideoUrl') if null_video else 'None found'}")

# Show all field names from one document to verify schema
sample_any = artworks.find_one({})
if sample_any:
    print(f"\nAll fields in a sample document:")
    for key in sample_any.keys():
        print(f"  - {key}")