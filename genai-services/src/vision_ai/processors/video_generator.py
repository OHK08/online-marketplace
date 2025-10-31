import os 
import time
import uuid
import cv2
import numpy as np
from pathlib import Path
from typing import Optional

class VeoGenerator:
    def __init__(self, project_id: str = "mock", use_mock: bool = True):
        self.project_id = project_id or "mock"
        self.use_mock = use_mock
        print(f"VeoGenerator initialized (Mock: {use_mock})")

    def generate_video(self, prompt: Optional[str] = None) -> str:
        if not prompt or not prompt.strip():
            prompt = "A glowing crystal fox runs across a neon forest, cartoon style, 5 seconds"
        prompt = prompt.strip()
        print(f"Generating video for: {prompt[:60]}...")
        time.sleep(2)
        return f"gs://mock-bucket/{uuid.uuid4().hex}.mp4"

    def _download_from_mock(self, gs_uri: str, prompt: str) -> str:
        local_dir = Path("C:/tmp")
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / f"veo_{uuid.uuid4().hex[:8]}.mp4"
        
        self._create_5sec_video(local_path, prompt)
        print(f"Video saved: {local_path}")
        return str(local_path)

    def _create_5sec_video(self, path: Path, prompt: str):
        width, height = 640, 360
        fps = 30
        duration = 5
        total_frames = fps * duration

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

        # Safe text
        main_text = "Veo Mock Video"
        subtext = (prompt[:47] + "...") if len(prompt) > 50 else prompt

        for _ in range(total_frames):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:] = (20, 20, 40)  # Dark blue

            cv2.putText(frame, main_text, (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
            cv2.putText(frame, subtext, (50, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 255), 1)

            out.write(frame)

        out.release()

    def generate_and_save(self, prompt: Optional[str] = None) -> str:
        gs_uri = self.generate_video(prompt)
        return self._download_from_mock(gs_uri, prompt or "Default animated scene")


# ONE-CLICK TEST
if __name__ == "__main__":
    gen = VeoGenerator(use_mock=True)
    
    # Test 1: Default
    path1 = gen.generate_and_save()
    print(f"VIDEO 1: {path1}")
    
    # Test 2: Custom
    path2 = gen.generate_and_save("A brave knight fights a dragon under purple sky")
    print(f"VIDEO 2: {path2}")
    
    # Test 3: None prompt
    path3 = gen.generate_and_save(None)
    print(f"VIDEO 3 (None): {path3}")
    
    print("\nOPEN: Start-Process 'C:\\tmp\\veo_*.mp4'")