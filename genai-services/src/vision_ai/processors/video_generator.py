# TODO: Veo video generator – will fill in next steps
import os
import time
import uuid
from google.cloud import aiplatform
from google.cloud.aiplatform import gapic as aiplatform_gapic

class VeoGenerator:
    def __init__(self, project_id: str, location: str = "us-central1"):
        aiplatform.init(project=project_id, location=location)
        self.project_id = project_id
        self.location = location
    def _get_endpoint(self):
        # Replace with your actual Veo endpoint name if different
        return f"projects/online-marketplace-476516/locations/asia-south1/publishers/google/models/veo"
    def generate_video(self, prompt: str = None) -> str:
        if prompt is None:
            prompt = "A glowing crystal fox runs across a neon forest, cartoon style, 5 seconds"

        endpoint_path = self._get_endpoint()
        endpoint = aiplatform.Endpoint(endpoint_path)

        instance = {"prompt": prompt}
        response = endpoint.predict(instances=[instance])

        # Async operation
        operation = response._operation
        print(f"Operation started: {operation.name}")

        # Poll
        client = aiplatform_gapic.PredictionServiceClient()
        while True:
            op = client.get_operation(operation.name)
            if op.done:
                break
            print("Polling... (10s)")
            time.sleep(10)

        # Extract video
        video_uri = op.response.value.predictions[0].bytesValue  # or check actual field
        # We'll handle download in next part
        return video_uri
    def _download_from_gs(self, gs_uri: str) -> str:
        import subprocess
        local_path = f"/tmp/veo_{uuid.uuid4().hex}.mp4"
        cmd = ["gsutil", "cp", gs_uri, local_path]
        subprocess.run(cmd, check=True)
        return local_path

    def generate_and_save(self) -> str:
        gs_uri = self.generate_video()
        return self._download_from_gs(gs_uri)
if __name__ == "__main__":
    gen = VeoGenerator(project_id=os.getenv("GCP_PROJECT_ID") or "online-marketplace-476516")
    path = gen.generate_and_save()
    print(f"SAVED: {path}")
if __name__ == "__main__":
    gen = VeoGenerator(project_id=os.getenv("GCP_PROJECT_ID") or "online-marketplace-476516D")
    path = gen.generate_and_save()
    print(f"SAVED: {path}")