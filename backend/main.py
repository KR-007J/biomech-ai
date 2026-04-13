import os
import cv2
import uuid
import shutil
import asyncio
from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from dotenv import load_dotenv

from pose_engine import PoseEngine
from biomechanics import get_biomechanical_analysis
from risk_engine import analyze_injury_risk

load_dotenv()

app = FastAPI(title="Biomech AI Backend")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Pose Engine
engine = PoseEngine()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# In-memory storage for analysis results (use DB for production)
analysis_results = {}

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload-video")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    analysis_results[job_id] = {"status": "processing", "progress": 0}
    background_tasks.add_task(process_video_task, job_id, file_path)
    
    return {"job_id": job_id, "status": "processing"}

@app.get("/results/{job_id}")
async def get_results(job_id: str):
    return analysis_results.get(job_id, {"error": "Job not found"})

async def process_video_task(job_id: str, file_path: str):
    cap = cv2.VideoCapture(file_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    frame_count = 0
    all_angles = []
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
            
        # Process every 5th frame to speed up (tunable)
        if frame_count % 5 == 0:
            keypoints, _ = engine.process_frame(frame)
            if keypoints:
                angles = get_biomechanical_analysis(keypoints)
                all_angles.append(angles)
        
        frame_count += 1
        # Update progress roughly
        analysis_results[job_id]["progress"] = int((frame_count / total_frames) * 100)
    
    cap.release()
    
    # Aggregate analysis
    if not all_angles:
        analysis_results[job_id] = {"status": "error", "message": "No pose detected in video"}
        return

    # Calculate average/peak angles
    avg_angles = {k: np.mean([a[k] for a in all_angles if k in a]) for k in all_angles[0].keys()}
    
    # Risk Assessment
    risk_info = analyze_injury_risk(avg_angles)
    
    # Gemini AI Feedback
    ai_feedback = "Enable Gemini API for personalized coaching."
    if model:
        prompt = f"""
        Act as a professional biomechanics coach. 
        Based on the technical analysis of a workout video:
        - Average Angles: {avg_angles}
        - Risk Level: {risk_info['risk_level']}
        - Risk Explanation: {risk_info['explanation']}
        
        Provide a concise (3-4 sentences), encouraging, and highly technical feedback to help the user improve their form and avoid injury.
        """
        try:
            response = model.generate_content(prompt)
            ai_feedback = response.text
        except Exception as e:
            ai_feedback = f"AI Feedback temporarily unavailable: {str(e)}"

    analysis_results[job_id] = {
        "status": "completed",
        "angles": avg_angles,
        "risk": risk_info,
        "feedback": ai_feedback,
        "summary": "Analysis complete. Review your metrics below."
    }
    
    # Clean up file
    # os.remove(file_path)

@app.get("/")
async def root():
    return {"message": "Biomech AI API is running"}
