import os
import re
import random
import httpx

# Load .env file
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="TheCircuit - AI Oracle Brain")

# Sample "Hackathon-style" Intelligence Logic
class Command(BaseModel):
    query: str
    context: str = "general"
    vendor_verified: bool = False
    org_onboarded: bool = False

@app.post("/analyze_intent")
async def analyze_intent(command: Command):
    """
    LOCAL AI ENGINE:
    This function replaces basic JS string matching with a Python-based 
    intent-classification logic. 
    In a real-world scenario, you'd use NLTK or SpaCy here.
    """
    q = command.query.lower()
    
    # INTENT MAPPING ENGINE
    intents = {
        "nav_vendor_dashboard": ["vendor dashboard", "vendor home", "my vendor dashboard", "vendor page"],
        "nav_org_dashboard": ["organiser dashboard", "organizer dashboard", "organiser home", "organizer page", "event dashboard"],
        "nav_tinder": ["matchmaker", "swipe", "invit", "tinder", "find vendor"],
        "nav_profile": ["profile", "account", "settings", "my stall"],
        "nav_messages": ["message", "chat", "talk", "conversation"],
        "nav_applications": ["application", "apply", "who applied"],
        "nav_matches": ["match", "show my matches", "my vendors"],
        "action_kyc": ["kyc", "verify", "aadhaar", "document"],
        "nav_overview": ["dashboard", "home", "overview", "stats"]
    }
    
    intent_found = "unknown"
    confidence = 0.0
    
    for intent, keywords in intents.items():
        score = sum(1 for kw in keywords if kw in q)
        if score > 0:
            current_conf = score / len(keywords)
            if current_conf > confidence:
                confidence = current_conf
                intent_found = intent
                
    response_map = {
        "nav_vendor_dashboard": "Entering your Vendor Dashboard now.",
        "nav_org_dashboard": "Opening the Organiser Portal for you.",
        "nav_tinder": "Connecting you to the Vendor Matchmaker deck. Let's find some stalls!",
        "nav_profile": "Opening your profile settings now.",
        "nav_messages": "Pulling up your active conversations.",
        "nav_applications": "Showing everyone who has applied for your event.",
        "nav_matches": "Displaying your confirmed matches and the coordination chat.",
        "action_kyc": "Preparing your secure eKYC verification environment.",
        "nav_overview": "Returning to your central executive dashboard.",
        "prompt_portal_choice": "Which dashboard would you like to open? The Vendor dashboard or the Organiser dashboard?",
        "unknown": "I'm processing that... I can help you with matching, profiles, or verification!"
    }
    
    # ===== DYNAMIC STATE & ACCESS LOGIC =====
    # If guest asks for anything generic, force them to choose a portal
    if command.context in ["guest", "", None]:
        if intent_found in ["nav_overview", "nav_profile", "nav_tinder", "nav_matches", "nav_applications", "nav_messages"]:
            if "vendor" in q:
                intent_found = "nav_vendor_dashboard"
            elif "organi" in q:
                intent_found = "nav_org_dashboard"
            else:
                intent_found = "prompt_portal_choice"
                
    # If they requested vendor functions, check if they need eKYC
    if intent_found in ["nav_vendor_dashboard"] or (command.context == "vendor" and intent_found in ["nav_overview", "nav_profile", "nav_matches"]):
        if not command.vendor_verified:
            intent_found = "action_kyc" # Force UI to open KYC
            response_map["action_kyc"] = "Your vendor profile is pending. Please complete your secure eKYC verification first!"
            
    # If they requested organiser functions, check if onboarded
    if intent_found in ["nav_org_dashboard", "nav_tinder", "nav_applications"] or (command.context == "organiser" and intent_found in ["nav_overview", "nav_profile", "nav_matches"]):
        if not command.org_onboarded:
            intent_found = "action_onboard_org"
            response_map["action_onboard_org"] = "You need to set up your Organiser details before I can show you that."

    response_text = response_map.get(intent_found, "I'm processing that... I can help with matching or eKYC verification.")            
    return {
        "intent": intent_found,
        "confidence": round(confidence * 100, 2),
        "response": response_text,
        "source": "Python-Native Brain v1.1"
    }

@app.get("/health")
def health():
    return {"status": "AI Oracle Online"}

class MatchRequest(BaseModel):
    vendor_cat: str
    event_cat: str
    vendor_city: str
    event_city: str

@app.post("/calculate_match")
async def calculate_match(data: MatchRequest):
    """
    MATCHING ENGINE:
    Simulates a vector-based similarity score for the hackathon demo.
    """
    score = 60 # Base score
    
    # Category Alignment
    if data.vendor_cat.lower() == data.event_cat.lower():
        score += 25
    elif data.vendor_cat.lower() in ["food", "beverage"] and data.event_cat.lower() in ["food", "festival"]:
        score += 15
        
    # Geographic Alignment
    if data.vendor_city.lower() == data.event_city.lower():
        score += 15
        
    # Random Variance for "Realism"
    score = min(99, score + random.randint(-5, 5))
    
    return {
        "score": score,
        "verdict": "High Potential" if score > 85 else "Strong Fit" if score > 70 else "Average Match",
        "algorithm": "Python Vector-Sim v2"
    }
# =====================================================================
#  SANDBOX.CO.IN AADHAAR OFFLINE eKYC
#  Step 1: POST /aadhaar/otp   → sends OTP to registered mobile
#  Step 2: POST /aadhaar/verify → submits OTP, returns verified data
# =====================================================================

SANDBOX_BASE       = "https://api.sandbox.co.in"
SANDBOX_API_KEY    = os.getenv("SANDBOX_API_KEY", "")
SANDBOX_API_SECRET = os.getenv("SANDBOX_API_SECRET", "")

_token_cache = {"token": None}

async def get_token() -> str:
    """Auto-fetch a fresh JWT — re-authenticates if token is missing."""
    if _token_cache["token"]:
        return _token_cache["token"]
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{SANDBOX_BASE}/authenticate",
            headers={
                "x-api-key":     SANDBOX_API_KEY,
                "x-api-secret":  SANDBOX_API_SECRET,
                "x-api-version": "2.0",
            }
        )
        body = resp.json()
        token = (body.get("data") or {}).get("access_token") or body.get("access_token")
        if not token:
            raise HTTPException(status_code=500, detail=f"Sandbox auth failed: {body}")
        _token_cache["token"] = token
        print(f"Sandbox token refreshed OK.")
        return token

async def sandbox_headers() -> dict:
    token = await get_token()
    return {
        "x-api-key":     SANDBOX_API_KEY,
        "Authorization": token,
        "x-api-version": "2.0",
        "Content-Type":  "application/json",
    }

class AadhaarOtpRequest(BaseModel):
    aadhaar_number: str   # 12-digit, no spaces

class AadhaarVerifyRequest(BaseModel):
    aadhaar_number: str
    otp:            str
    ref_id:         str   # returned from /aadhaar/otp step

@app.post("/aadhaar/otp")
async def aadhaar_send_otp(req: AadhaarOtpRequest):
    """
    Step 1 — Send OTP to the mobile number registered with Aadhaar.
    Returns ref_id needed for the verify step.
    """
    clean = re.sub(r'\s+', '', req.aadhaar_number)
    if not re.fullmatch(r'\d{12}', clean):
        raise HTTPException(status_code=400, detail="Aadhaar number must be exactly 12 digits")

    payload = {
        "@entity":        "in.co.sandbox.kyc.aadhaar.okyc.otp.request",
        "aadhaar_number": clean,
        "consent":        "y",
        "reason":         "For KYC on TheCircuit"
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{SANDBOX_BASE}/kyc/aadhaar/okyc/otp",
            headers=await sandbox_headers(),
            json=payload
        )

    body = resp.json()

    if resp.status_code == 401:
        _token_cache["token"] = None  # force re-auth next call
        raise HTTPException(status_code=401, detail="Sandbox token expired — please retry")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code,
                            detail=body.get("message", "Sandbox OTP request failed"))

    ref_id = body.get("data", {}).get("ref_id") or body.get("ref_id")
    return {
        "success": True,
        "ref_id":  ref_id,
        "message": body.get("data", {}).get("message", "OTP sent successfully")
    }


@app.post("/aadhaar/verify")
async def aadhaar_verify_otp(req: AadhaarVerifyRequest):
    """
    Step 2 — Submit the OTP. On success returns verified name, DOB,
    address, gender, and photo (base64) straight from UIDAI via Sandbox.
    """
    payload = {
        "@entity":        "in.co.sandbox.kyc.aadhaar.okyc.otp.verify.request",
        "aadhaar_number": re.sub(r'\s+', '', req.aadhaar_number),
        "otp":            req.otp,
        "ref_id":         req.ref_id
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{SANDBOX_BASE}/kyc/aadhaar/okyc/otp/verify",
            headers=await sandbox_headers(),
            json=payload
        )

    body = resp.json()

    if resp.status_code == 401:
        _token_cache["token"] = None
        raise HTTPException(status_code=401, detail="Sandbox token expired — please retry")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code,
                            detail=body.get("message", "OTP verification failed"))

    data = body.get("data", {})
    return {
        "success": True,
        "data": {
            "name":           data.get("name"),
            "dob":            data.get("dob"),
            "gender":         data.get("gender"),
            "address":        data.get("address", {}),
            "photo":          data.get("photo"),   # base64 photo from UIDAI
            "aadhaar_number": re.sub(r'\s+', '', req.aadhaar_number),
        }
    }


if __name__ == "__main__":
    print("🧠 TheCircuit AI Brain is waking up on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)