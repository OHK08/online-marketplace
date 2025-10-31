import os
import json
import uuid
import logging
from pathlib import Path  # ← FIXED: Was missing!
import time
from google.cloud import storage
import google.generativeai as genai
import cv2
import numpy as np
from scipy.io.wavfile import write
from pathlib import Path

# V2 PROMPT
from src.vision_ai.prompts.prompt_engineering import story_to_veo_prompt_v2

logger = logging.getLogger(__name__)

class VeoGenerator:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("GCP_LOCATION", "asia-south1")
        self.bucket_name = os.getenv("GCP_BUCKET")
        self.output_dir = Path("C:/tmp")
        self.output_dir.mkdir(exist_ok=True)
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    def generate_and_save(self, story_json: str) -> str:
        story = json.loads(story_json)
        prompt = story_to_veo_prompt_v2(story_json)
        logger.info(f"V E O Prompt: {prompt[:200]}...")
        video_path = self._generate_veo_video(prompt)
        audio_path = self._generate_silent_audio()
        final_path = self._merge_video_audio(video_path, audio_path)
        video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)
        return str(final_path)

    def _generate_veo_video(self, prompt: str) -> Path:
        try:
            from google.cloud import aiplatform
            from google.cloud.aiplatform_v1.types import PredictRequest

            endpoint = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/veo-3.1-generate-preview"
            client = aiplatform.PredictionServiceClient()

            request = PredictRequest(
                endpoint=endpoint,
                instances=[{"prompt": prompt}],
                parameters={
                    "duration": 8,
                    "aspect_ratio": "16:9",
                    "fps": 24,
                    "resolution": "1080p",
                    "storageUri": f"gs://{self.bucket_name}/veo_outputs/"
                }
            )

            logger.info("Calling V E O 3.1...")
            response = client.predict_long_running(request=request)
            operation = response.operation

            while not operation.done():
                time.sleep(10)
                operation = client.get_operation(operation.name)
                logger.info("V E O polling...")

            video_uri = operation.response.predictions[0]['videoUri']
            logger.info(f"V E O ready: {video_uri}")

            video_path = self.output_dir / f"veo_{uuid.uuid4().hex}.mp4"
            storage_client = storage.Client(project=self.project_id)
            bucket = storage_client.bucket(self.bucket_name)
            blob_name = video_uri.split('/')[-1]
            blob = bucket.blob(f"veo_outputs/{blob_name}")
            blob.download_to_filename(str(video_path))
            return video_path

        except Exception as e:
            logger.error(f"V E O failed: {e} → using mock")
            return self._create_mock_video(prompt)

    def _create_mock_video(self, prompt: str) -> Path:
        video_path = self.output_dir / f"mock_{uuid.uuid4().hex}.mp4"
        w, h = 1280, 720
        fps = 24
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, fps, (w, h))
        bg = np.full((h, w, 3), (0, 140, 255), dtype=np.uint8)
        lines = self._wrap_text(prompt[:120], w - 100)
        for _ in range(8 * fps):
            frame = bg.copy()
            y = 200
            for line in lines:
                (tw, th), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 1.1, 2)
                x = (w - tw) // 2
                cv2.putText(frame, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255,255,255), 2, cv2.LINE_AA)
                y += int(th * 1.6)
            out.write(frame)
        out.release()
        return video_path

    def _wrap_text(self, text: str, max_w: int):
        words = text.split()
        lines, line = [], ""
        for word in words:
            test = line + word + " "
            (w, _), _ = cv2.getTextSize(test, cv2.FONT_HERSHEY_SIMPLEX, 1.1, 2)
            if w < max_w: line = test
            else: lines.append(line); line = word + " "
        lines.append(line)
        return lines

    def _generate_silent_audio(self) -> Path:
        audio_path = self.output_dir / f"silent_{uuid.uuid4().hex}.wav"
        write(str(audio_path), 44100, np.zeros(int(44100 * 8), dtype=np.int16))
        return audio_path

    def _merge_video_audio(self, video_path: Path, audio_path: Path) -> Path:
        final_path = self.output_dir / f"final_veo_{uuid.uuid4().hex}.mp4"
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(final_path), fourcc, fps, (w, h))
        while True:
            ret, frame = cap.read()
            if not ret: break
            out.write(frame)
        cap.release(); out.release()
        return final_path


# PUBLIC HELPER
def generate_veo_video_with_v2_prompt(story_json: str) -> str:
    return VeoGenerator().generate_and_save(story_json)