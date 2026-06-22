from fastapi import APIRouter, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import shutil

router = APIRouter()

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Upload limit check logic is usually done in middleware or server config.
# For FastAPI, UploadFile handles streaming, but we can set MAX_UPLOAD_SIZE if needed.

@router.get("/upload")
async def upload_page(request: Request):
    return templates.TemplateResponse(request=request, name="upload.html")

def process_upload_task(file_path: Path, video_number: str, video_title: str):
    from backend.transcription import get_whisper_model, process_video
    from backend.embeddings import get_embedding_model, get_qdrant_client, reindex_all
    
    root = Path(__file__).parent.parent
    videos_dir = root / "videos"
    audios_dir = root / "audios"
    jsons_dir = root / "jsons"
    
    whisper_model = get_whisper_model()
    # Process video
    try:
        res = process_video(
            video_path=file_path,
            video_number=video_number,
            video_title=video_title,
            whisper_model=whisper_model,
            videos_dir=videos_dir,
            audios_dir=audios_dir,
            jsons_dir=jsons_dir,
            language="hi",
            task="translate"
        )
        # Re-index all in Qdrant
        q_client, err = get_qdrant_client()
        if q_client:
            embed_model = get_embedding_model()
            reindex_all(jsons_dir, q_client, embed_model)
    except Exception as e:
        print(f"Error processing video: {e}")

@router.post("/api/upload")
async def handle_upload(
    request: Request,
    background_tasks: BackgroundTasks,
    video_number: str = Form(...),
    video_title: str = Form(...),
    file: UploadFile = File(...)
):
    # 100MB check (naive approach: check content-length header if provided, 
    # but for true security requires reading in chunks)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 100 * 1024 * 1024:
        return HTMLResponse("<div class='text-red-500'>File too large (Max 100MB)</div>", status_code=400)
        
    videos_dir = Path(__file__).parent.parent / "videos"
    videos_dir.mkdir(exist_ok=True)
    
    safe_filename = file.filename.replace(" ", "_")
    file_path = videos_dir / safe_filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    background_tasks.add_task(process_upload_task, file_path, video_number, video_title)
    
    return HTMLResponse(
        "<div class='text-green-500 font-medium'>Upload successful! Video is processing in the background...</div>"
    )
