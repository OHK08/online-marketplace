# ============================================================================
# FILE: veo-api-service/api/gcs_client.py
# ============================================================================
from google.cloud import storage
from datetime import datetime, timedelta
from .config import config
import re
import google.auth
from google.auth.transport import requests as auth_requests
import google.auth.iam
import google.auth.compute_engine.credentials

_gcs_client = None

def get_gcs_client():
    """Get GCS client singleton"""
    global _gcs_client
    if _gcs_client is None:
        _gcs_client = storage.Client(project=config.GCP_PROJECT_ID)
    return _gcs_client

def parse_gs_uri(gs_uri: str) -> tuple:
    """
    Parse a gs:// URI into bucket name and blob name.
    
    Args:
        gs_uri: A GCS URI like "gs://bucket-name/path/to/file.mp4"
    
    Returns:
        tuple: (bucket_name, blob_name)
    """
    match = re.match(r'^gs://([^/]+)/(.+)$', gs_uri)
    if not match:
        raise ValueError(f"Invalid GCS URI format: {gs_uri}")
    
    bucket_name = match.group(1)
    blob_name = match.group(2)
    return bucket_name, blob_name

def generate_signed_url(gs_uri: str) -> str:
    """
    Generate a signed URL for a GCS object using IAM-based signing.
    This works with Cloud Run's Workload Identity without needing a private key.
    
    Args:
        gs_uri: A GCS URI like "gs://bucket-name/path/to/file.mp4"
    
    Returns:
        str: A public HTTPS URL with authentication parameters
    """
    try:
        # Parse the GCS URI
        bucket_name, blob_name = parse_gs_uri(gs_uri)
        
        # Get credentials and signing method
        credentials, project = google.auth.default()
        
        # Create IAM signer using the service account
        service_account_email = f"veo-api-sa@{config.GCP_PROJECT_ID}.iam.gserviceaccount.com"
        
        # For Cloud Run, we need to use IAM-based signing
        if isinstance(credentials, google.auth.compute_engine.credentials.Credentials):
            # Use IAM API to sign
            auth_request = auth_requests.Request()
            credentials.refresh(auth_request)
            
            # Create a signing function using IAM
            signer = google.auth.iam.Signer(
                request=auth_request,
                credentials=credentials,
                service_account_email=service_account_email
            )
            
            # Create signing credentials
            signing_credentials = google.auth.compute_engine.IDTokenCredentials(
                request=auth_request,
                target_audience="",
                signer=signer,
                service_account_email=service_account_email
            )
        else:
            signing_credentials = credentials
        
        # Get GCS client and blob
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        # Generate signed URL with expiration
        expiration = timedelta(hours=config.SIGNED_URL_EXPIRATION_HOURS)
        
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration,
            method="GET",
            service_account_email=service_account_email,
            credentials=signing_credentials
        )
        
        return signed_url
    
    except Exception as e:
        raise Exception(f"Failed to generate signed URL for {gs_uri}: {str(e)}")
