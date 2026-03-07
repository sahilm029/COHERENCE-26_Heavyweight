import os
import requests
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

BLAND_API_KEY = os.getenv("BLAND_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN") # e.g. "abcdef123.ngrok.app"

def trigger_bland_call(to_phone: str, franchise_name: str, franchise_id: int):
    """
    Sends a REST API request to Bland to trigger an outbound call to the lead.
    """
    if not BLAND_API_KEY:
        return {"error": "Missing BLAND_API_KEY in environment"}
        
    url = "https://api.bland.ai/v1/calls"
    
    headers = {
        "authorization": BLAND_API_KEY,
        "Content-Type": "application/json"
    }
    
    # User Requirements:
    # 1. Persona: Sarah Chen, Senior Growth Specialist.
    # 2. Goal: Qualify lead for franchise opportunity. Schedule 10-min briefing tomorrow at 2 PM. Tell them WhatsApp confirmation is sent.
    # 3. Voice: Female, en-IN, reduce_latency=true
    # 4. First Sentence: "Hello, I'm Sarah Chen calling from {franchise_name}. Am I speaking with the business owner?"
    
    prompt = (
        "You are Sarah Chen, a Senior Growth Specialist. "
        "Your goal is to qualify the lead for a franchise opportunity. "
        "If they are interested, schedule a 10-minute briefing for tomorrow at 2 PM. "
        "If they agree to the briefing, tell them a WhatsApp confirmation is being sent."
    )
    
    first_sentence = f"Hello, I'm Sarah Chen calling from {franchise_name}. Am I speaking with the business owner?"
    
    # We pass franchise_id in metadata so the webhook knows which franchise this lead belongs to.
    payload = {
        "phone_number": to_phone,
        "task": prompt,
        "first_sentence": first_sentence,
        "voice": "maya", # En-US/IN equivalent for Bland. 'public/en-US-neural-1' isn't explicitly defined in Bland's quick list without a voice_id, so we use their standard Maya voice.
        "language": "en",
        "reduce_latency": True,
        "record": True,
        "webhook": f"https://{NGROK_DOMAIN}/webhook/bland" if NGROK_DOMAIN else None,
        "metadata": {
            "franchise_id": franchise_id,
            "franchise_name": franchise_name
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            data = response.json()
            return {"status": "success", "call_id": data.get("call_id")}
        else:
            print(f"[BLAND API ERROR] {response.status_code} - {response.text}")
            return {"error": f"Bland API Error {response.status_code}: {response.text}"}
            
    except requests.exceptions.RequestException as e:
        print(f"[BLAND REQUEST ERROR] {e}")
        return {"error": str(e)}

def send_whatsapp_notification(franchise_name: str, whatsapp_number: str, message_body: str = None):
    """
    Triggers twilio WhatsApp API.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("[TWILIO] Missing credentials.")
        return False
        
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    if not whatsapp_number.startswith("whatsapp:"):
        whatsapp_number = f"whatsapp:{whatsapp_number}"
        
    from_whatsapp = TWILIO_WHATSAPP_NUMBER
    if from_whatsapp and not from_whatsapp.startswith("whatsapp:"):
        from_whatsapp = f"whatsapp:{from_whatsapp}"
        
    if not message_body:
        message_body = f"✅ *Franchise Alert ({franchise_name})*\nA lead has confirmed their interest and booked a 10-minute briefing for tomorrow at 2 PM. Please check your dashboard for the call transcript."
    
    try:
        message = client.messages.create(
            body=message_body,
            from_=from_whatsapp,
            to=whatsapp_number
        )
        print(f"[WHATSAPP] Sent to {whatsapp_number}. SID: {message.sid}")
        return True
    except Exception as e:
        print(f"[WHATSAPP ERROR] {e}")
        return False
