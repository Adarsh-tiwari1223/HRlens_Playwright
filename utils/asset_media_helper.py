"""
Asset Media Helper Utility for HRlens Playwright Automation.
Provides static media file paths conforming to:
- Photos: Up to 4 photos (each <= 5MB max)
- Video: 1 video (10s length)
"""

import os
import logging

logger = logging.getLogger(__name__)


def get_return_test_media_files(include_video: bool = True, max_photos: int = 4) -> list[str]:
    """
    Returns a list of absolute file paths for return media attachments:
    - Up to 4 valid image files (each <= 5MB)
    - 1 valid 10-second video file (if include_video=True)
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    candidate_images = [
        os.path.join(base_dir, "testdata", "static", "image", "file_example_JPG_2500kB.jpg"),
        os.path.join(base_dir, "testdata", "static", "image", "file_example_PNG_3MB.png"),
        os.path.join(base_dir, "testdata", "static", "image", "4mb-Image-file-Download.png"),
        os.path.join(base_dir, "testdata", "static", "image", "Sample-Image-file-Download.jpg"),
        os.path.join(base_dir, "testdata", "static", "image", "varanasi 2.jpg"),
        os.path.join(base_dir, "testdata", "static", "image", "Chitrakote_Falls.jpg")
    ]
    
    candidate_videos = [
        os.path.join(base_dir, "testdata", "static", "video", "sample-mp4-file-500kb.mp4"),
        os.path.join(base_dir, "testdata", "static", "video", "file_example_MP4_1280_10MG.mp4")
    ]

    selected_files = []
    
    # 1. Collect up to max_photos valid image files
    for img_path in candidate_images:
        if os.path.exists(img_path):
            file_size_mb = os.path.getsize(img_path) / (1024 * 1024)
            if file_size_mb <= 5.05: # <= 5MB
                selected_files.append(img_path)
                if len(selected_files) >= max_photos:
                    break

    # 2. Collect 1 video file (~10s)
    if include_video:
        for vid_path in candidate_videos:
            if os.path.exists(vid_path):
                selected_files.append(vid_path)
                break

    logger.info(f"[RETURN MEDIA HELPER] Prepared {len(selected_files)} media files for return attachment: {[os.path.basename(f) for f in selected_files]}")
    return selected_files
