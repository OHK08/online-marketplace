import os
import google.auth
from fastapi import FastAPI, Request, HTTPException
from google.cloud import run_v2

app = FastAPI()

# Get project info from environment
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
GCP_REGION = os.environ.get("GCP_REGION")
JOB_NAME = os.environ.get("JOB_NAME")

# Get the full job name
job_path = f"projects/{GCP_PROJECT_ID}/locations/{GCP_REGION}/jobs/{JOB_NAME}"

# Initialize the client
try:
    client = run_v2.JobsClient()
except Exception as e:
    print(f"CRITICAL: Failed to initialize JobsClient: {e}")
    client = None

@app.post("/")
async def trigger_job(request: Request):
    """
    Receives a Pub/Sub message and triggers the Cloud Run Job.
    """
    if not client:
        print("Error: JobsClient not initialized.")
        raise HTTPException(status_code=500, detail="Job client not initialized")

    try:
        # You can optionally parse the Pub/Sub message, but we don't need to.
        # body = await request.json() 
        
        print(f"Trigger request received for job: {job_path}")

        # Make the API call to run the job
        # We run this asynchronously and return OK to Pub/Sub immediately.
        request = run_v2.RunJobRequest(name=job_path)
        client.run_job(request=request)
        
        print(f"Job trigger call for {job_path} succeeded.")
        return {"message": "Job triggered"}, 200

    except Exception as e:
        print(f"Error triggering job: {e}")
        raise HTTPException(status_code=500, detail=f"Error triggering job: {e}")