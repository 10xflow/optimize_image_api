import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from utils.image_processor import get_max_dimensions, resize_image
import shutil
import os
import base64
import json
from datetime import datetime

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
    logs_only: bool = Query(False, description="Return logs instead of image"),
):
    logs = []
    def log(step, msg):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "step": step,
            "message": msg
        }
        logs.append(log_entry)
        logger.info(f"{step}: {msg}")

    try:
        log("request", f"Received request: blog_name={blog_name}, image_type={image_type}, filename={image.filename}")

        contents = await image.read()
        log("read", f"Read {len(contents)} bytes from uploaded image.")

        # Get max dimensions for the blog and image type
        max_w, max_h = get_max_dimensions(blog_name, image_type)
        log("dimensions", f"Max dimensions for {blog_name} ({image_type}): width={max_w}, height={max_h}")

        # Resize and compress
        resized_image_io, resize_logs = resize_image(contents, max_w, max_h, return_logs=True)
        logs.extend(resize_logs)
        log("done", "Image resized successfully.")

        if logs_only:
            return JSONResponse(content={"logs": logs})

        # Add logs to response header as JSON (truncated for header safety)
        log_json = json.dumps(logs)[-4000:]
        return StreamingResponse(
            resized_image_io,
            media_type="image/jpeg",
            headers={"X-Process-Logs": log_json}
        )

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        logs.append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "step": "error",
            "message": str(e)
        })
        return JSONResponse(status_code=400, content={"logs": logs, "error": str(e)})
