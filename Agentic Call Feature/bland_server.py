from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import database
from bland_telephony import trigger_bland_call, send_whatsapp_notification
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = FastAPI(title="OutreachOS Bland Integration")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

@app.on_event("startup")
def startup_event():
    database.init_db()

class FranchiseCreate(BaseModel):
    name: str
    whatsapp: str

class CallRequest(BaseModel):
    franchise_id: int
    to_phone: str

@app.post("/api/franchises")
def register_franchise(franchise: FranchiseCreate):
    fid = database.create_franchise(franchise.name, franchise.whatsapp)
    return {"status": "success", "franchise_id": fid}

@app.get("/api/franchises")
def list_franchises():
    return database.get_franchises()

@app.post("/api/initiate-call")
def initiate_call(req: CallRequest):
    franchise = database.get_franchise(req.franchise_id)
    if not franchise:
        raise HTTPException(status_code=404, detail="Franchise not found")
        
    res = trigger_bland_call(req.to_phone, franchise["name"], req.franchise_id)
    
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
        
    call_id = res["call_id"]
    database.create_call_record(call_id, req.franchise_id, req.to_phone)
    return {"status": "success", "call_id": call_id, "message": "Bland AI call dispatched!"}

def analyze_transcript(transcript: str) -> bool:
    """Uses Gemini to determine if a meeting was booked."""
    if not gemini_client:
        # Fallback to simple keyword check if Gemini isn't available
        lower_tx = transcript.lower()
        words = ["yes", "book", "meeting", "briefing", "tomorrow", "2 pm", "sure", "sounds good", "okay"]
        return any(w in lower_tx for w in words)
        
    prompt = (
        "You are an expert sales analyst. Read the following call transcript and determine "
        "if the lead explicitly agreed to book a 10-minute briefing (or meeting) for tomorrow. "
        "Reply ONLY with the word TRUE or FALSE.\n\n"
        f"Transcript:\n{transcript}"
    )
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
        )
        return "true" in response.text.strip().lower()
    except Exception as e:
        print(f"[Gemini Webhook Error] {e}")
        return False

@app.post("/webhook/bland")
async def bland_webhook(request: Request):
    """
    Receives the end-of-call payload from Bland.
    Analyzes the transcript to see if a meeting was booked.
    """
    try:
        payload = await request.json()
        print(f"[WEBHOOK] Received payload from Bland: {payload.get('call_id')}")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
        
    call_id = payload.get("call_id")
    transcript = payload.get("concatenated_transcript") or payload.get("transcript") or ""
    
    # Metadata contains the franchise_id we injected at call trigger
    metadata = payload.get("metadata", {})
    franchise_id = metadata.get("franchise_id")
    franchise_name = metadata.get("franchise_name")
    
    if not call_id:
        return {"status": "ignored", "reason": "No call_id found"}
        
    # Analyze transcript
    meeting_booked = analyze_transcript(transcript)
    
    status = "completed" if payload.get("completed") else "failed"
    database.update_call_record(call_id, status, transcript, meeting_booked)
    
    if meeting_booked and franchise_id:
        # Get the destination WhatsApp number
        franchise = database.get_franchise(franchise_id)
        if franchise:
            notify_number = franchise["whatsapp"]
            msg = f"🚀 *Meeting Booked! ({franchise_name})*\nThe AI successfully booked a 10-minute briefing for tomorrow at 2 PM.\n\nTranscript Excerpt: {transcript[-200:]}"
            send_whatsapp_notification(franchise_name, notify_number, msg)
            
    return {"status": "success"}

@app.get("/api/history")
def get_history():
    return database.get_call_history()
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bland_server:app", host="0.0.0.0", port=8002, reload=True)
