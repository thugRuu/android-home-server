import os
import subprocess
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi import WebSocket, WebSocketDisconnect


app = FastAPI(title="Android Home Server")

# Folders for storage and media
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
MEDIA_DIR = BASE_DIR / "media"

for folder in [UPLOAD_DIR, MEDIA_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

class TaskRequest(BaseModel):
    command: str

@app.get("/")
def home():
    return {"message": "Android Python Server is running!"}

@app.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1. Extract the file extension (e.g., ".txt" becomes "txt")
    # If the filename has no extension, default to "others"
    file_extension = Path(file.filename).suffix.lower().lstrip(".")
    
    if not file_extension:
        folder_name = "others"
    else:
        folder_name = file_extension

    # 2. Create the target subfolder inside uploads if it doesn't exist
    target_folder = UPLOAD_DIR / folder_name
    target_folder.mkdir(parents=True, exist_ok=True)

    # 3. Read and save the file into that extension-specific folder
    file_path = target_folder / file.filename
    contents = await file.read()
    
    with open(file_path, "wb") as f:
        f.write(contents)

    return {
        "message": "File uploaded and organized by extension successfully!",
        "filename": file.filename,
        "extension_folder": folder_name
    }
# 1. FILE STORAGE: List Files (updated to show categories)
@app.get("/files")
def list_files():
    # Recursively find all files inside uploads and its subfolders
    all_files = []
    for path in UPLOAD_DIR.rglob("*"):
        if path.is_file():
            # Get relative path so you see the folder structure (e.g., "notes/todo.txt")
            all_files.append(str(path.relative_to(UPLOAD_DIR)))
    return {"files": all_files}

# 2. CPU TASK OFFLOAD: Run shell or script commands
@app.post("/task/run")
def run_cpu_task(task: TaskRequest):
    try:
        result = subprocess.run(
            task.command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Task timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/uploads/{folder}/{filename}")
def get_uploaded_file(folder: str, filename: str):
    file_path = UPLOAD_DIR / folder / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)




# Simple connection manager to broadcast frames if needed
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: bytes):
        for connection in self.active_connections:
            await connection.send_bytes(data)

manager = ConnectionManager()

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive raw image/frame data sent from the browser
            data = await websocket.receive_bytes()
            
            # Here you can process the data (e.g., run OpenCV, save frames, or broadcast)
            # For demonstration, we broadcast incoming frames to all connected clients:
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

from fastapi.responses import HTMLResponse

@app.get("/cam", response_class=HTMLResponse)
def camera_switcher_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Camera Switcher & Streamer</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="background: #111; color: #fff; text-align: center; font-family: sans-serif; padding-top: 20px;">
        <h2>Live Camera Streamer</h2>
        <div>
            <button id="switchBtn" style="padding: 10px 20px; font-size: 16px; cursor: pointer; margin-bottom: 15px; background: #333; color: #fff; border: 1px solid #555; border-radius: 5px;">Switch Camera</button>
        </div>
        <video id="video" autoplay playsinline style="display: none;"></video>
        <canvas id="canvas" width="640" height="480" style="max-width: 100%; border: 2px solid #444; border-radius: 8px;"></canvas>
        <p id="status">Connecting...</p>

        <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const status = document.getElementById('status');
            const switchBtn = document.getElementById('switchBtn');

            let currentStream = null;
            // Track facing mode: "environment" (back) or "user" (front)
            let useFrontCamera = false; 

            const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            const ws = new WebSocket(`${wsProtocol}//${location.host}/ws/stream`);

            ws.onopen = () => {
                status.innerText = "WebSocket Connected.";
                startCamera();
            };

            async function startCamera() {
                // Stop any existing stream before opening a new one
                if (currentStream) {
                    currentStream.getTracks().forEach(track => track.stop());
                }

                const constraints = {
                    video: {
                        width: { ideal: 640 },
                        height: { ideal: 480 },
                        facingMode: useFrontCamera ? "user" : "environment"
                    },
                    audio: false
                };

                try {
                    currentStream = await navigator.mediaDevices.getUserMedia(constraints);
                    video.srcObject = currentStream;
                    
                    video.onloadedmetadata = () => {
                        status.innerText = `Streaming (${useFrontCamera ? 'Front' : 'Back'} Camera)...`;
                    };
                } catch (err) {
                    status.innerText = "Camera Error: " + err.message;
                }
            }

            // Flip camera on button click
            switchBtn.onclick = () => {
                useFrontCamera = !useFrontCamera;
                startCamera();
            };

            // Stream frames to WebSocket every 100ms
            setInterval(() => {
                if (ws.readyState === WebSocket.OPEN && video.readyState === video.HAVE_ENOUGH_DATA) {
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                    canvas.toBlob((blob) => {
                        if (blob) ws.send(blob);
                    }, 'image/jpeg', 0.6);
                }
            }, 100);
        </script>
    </body>
    </html>
    """