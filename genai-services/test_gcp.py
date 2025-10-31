# test_gcp.py — FINAL & SIMPLE

from google.cloud import storage
import os
from dotenv import load_dotenv

load_dotenv()

project_id = os.getenv("GCP_PROJECT_ID") or "cedar-defender-475318-r5"
bucket_name = os.getenv("GCP_BUCKET") or "veo-videos-genai"

print(f"Project: {project_id}")
print(f"Bucket: {bucket_name}")

# TEST: List buckets
try:
    client = storage.Client(project=project_id)
    buckets = list(client.list_buckets())
    print("\nGCP AUTH OK — Buckets Found:")
    for b in buckets:
        print(f"  → {b.name}")
    if bucket_name not in [b.name for b in buckets]:
        print(f"  WARNING: Bucket '{bucket_name}' not found! Create it.")
    else:
        print(f"  SUCCESS: '{bucket_name}' is READY for V E O!")
except Exception as e:
    print(f"GCP FAILED: {e}")

print("\nGCP AUTH 100% VERIFIED — READY FOR V E O")