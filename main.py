import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from utils.image_processor import get_max_dimensions, resize_image
import shutil
import os
import base64

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/resize-image/")
async def resize_image_api(
    image: UploadFile = File(...),
    blog_name: str = Form(...),
    image_type: str = Form(...),  # "Hauptbild" or "Zusatzbild"
):
    logs = []
    def log(msg):
        logs.append(msg)
        logger.info(msg)

    try:
        log(f"Received request: blog_name={blog_name}, image_type={image_type}, filename={image.filename}")

        contents = await image.read()
        log(f"Read {len(contents)} bytes from uploaded image.")

        # Get max dimensions for the blog and image type
        max_w, max_h = get_max_dimensions(blog_name, image_type)
        log(f"Max dimensions for {blog_name} ({image_type}): width={max_w}, height={max_h}")

        # Resize and compress
        resized_image_io, _ = resize_image(contents, max_w, max_h, return_logs=True)
        log("Image resized successfully.")

        # Add logs to response header (truncated for header safety)
        log_str = " | ".join(logs)[-4000:]  # Truncate to last 4000 chars
        return StreamingResponse(
            resized_image_io,
            media_type="image/jpeg",
            headers={"X-Process-Logs": log_str}
        )

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        logs.append(f"Error: {e}")
        return JSONResponse(status_code=400, content={"logs": logs, "error": str(e)})
