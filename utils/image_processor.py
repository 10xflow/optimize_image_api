from PIL import Image
import os
import pandas as pd
from io import BytesIO
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Load blog size CSV once
CSV_PATH = os.path.join(os.path.dirname(__file__), 'blog_sizes.csv')
size_df = pd.read_csv(CSV_PATH)
logger.info(f"Loaded blog sizes from {CSV_PATH}")

def get_max_dimensions(blog_name: str, image_type: str) -> tuple[int, int]:
    logger.info(f"Fetching dimensions for blog: {blog_name}, image_type: {image_type}")
    row = size_df[size_df['Blog'] == blog_name]
    if row.empty:
        logger.error(f"Blog '{blog_name}' not found in CSV.")
        raise ValueError(f"Blog '{blog_name}' not found in CSV.")

    if image_type == "Hauptbild":
        width = int(row.iloc[0]["Hauptbild_Breite"])
        height = int(row.iloc[0]["Hauptbild_Höhe"])
    elif image_type == "Zusatzbild":
        width = int(row.iloc[0]["Zusatzbild_Breite"])
        height = int(row.iloc[0]["Zusatzbild_Höhe"])
    else:
        logger.error(f"Invalid image_type: {image_type}")
        raise ValueError("image_type must be 'Hauptbild' or 'Zusatzbild'.")

    logger.info(f"Dimensions found: width={width}, height={height}")
    return width, height

def resize_image(image_bytes: bytes, max_width: int, max_height: int, return_logs=False):
    logs = []
    def log(step, msg):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "step": step,
            "message": msg
        }
        logs.append(log_entry)
        logger.info(f"{step}: {msg}")

    log("resize_start", f"Starting image resize: max_width={max_width}, max_height={max_height}")
    original_size = len(image_bytes)
    log("original_size", f"Original file size: {original_size} bytes")
    img = Image.open(BytesIO(image_bytes))
    original_width, original_height = img.size
    log("original_dimensions", f"Original image size: width={original_width}, height={original_height}")

    aspect_ratio = original_width / original_height
    if original_width >= original_height:
        new_width = min(original_width, max_width)
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = min(original_height, max_height)
        new_width = int(new_height * aspect_ratio)

    log("resize_dimensions", f"Resizing to: width={new_width}, height={new_height}")
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    output_buffer = BytesIO()
    resized_img.save(output_buffer, format="JPEG", quality=85, optimize=True)
    output_buffer.seek(0)
    optimized_size = output_buffer.getbuffer().nbytes
    log("optimized_size", f"Optimized file size: {optimized_size} bytes")
    log("reduction", f"File size reduction: {original_size - optimized_size} bytes ({100 * (1 - optimized_size/original_size):.2f}% smaller)")
    log("resize_complete", "Image resize and save complete.")

    if return_logs:
        return output_buffer, logs
    return output_buffer
