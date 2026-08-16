from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import openai
import os
import time
import hashlib
import hmac
import requests
import re
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)
openai.api_key = os.getenv("OPENAI_KEY")
PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET_KEY")

class Prompt(BaseModel):
    user_id: str
    message: str
    project_id: str = None

class InitPayment(BaseModel):
    user_id: str
    email: str
    plan: str

# --- POINTS CHECK ---
@app.get("/user-points/{user_id}")
async def get_points(user_id: str):
    profile = supabase.table("profiles").select("points").eq("id", user_id).execute()
    if not profile.data:
        return {"points": 0}
    return {"points": profile.data[0]["points"]}

# --- PAYSTACK INIT ---
@app.post("/init-payment")
async def init_payment(data: InitPayment):
    plan_prices = {
        "premium": {"amount": 1500 * 100, "points": 10.5},
        "pro": {"amount": 3000 * 100, "points": 25}
    }
    if data.plan not in plan_prices:
        raise HTTPException(400, "Invalid plan")
    
    payload = {
        "email": data.email,
        "amount": plan_prices[data.plan]["amount"],
        "reference": f"vibe-{data.user_id[:8]}-{int(time.time())}",
        "callback_url": "https://your-frontend.vercel.app/payment-callback"
    }
    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET}"}
    resp = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)
    
    # Save transaction
    supabase.table("transactions").insert({
        "user_id": data.user_id,
        "amount": plan_prices[data.plan]["amount"] // 100,
        "points_added": plan_prices[data.plan]["points"],
        "reference": payload["reference"],
        "status": "pending"
    }).execute()
    
    return resp.json()

# --- PAYSTACK WEBHOOK ---
@app.post("/paystack-webhook")
async def paystack_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-paystack-signature")
    if not signature:
        raise HTTPException(400, "No signature")
    
    expected = hmac.new(PAYSTACK_SECRET.encode(), body, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(401, "Invalid signature")
    
    event = await request.json()
    if event["event"] == "charge.success":
        ref = event["data"]["reference"]
        tx = supabase.table("transactions").select("*").eq("reference", ref).execute()
        if not tx.data:
            return {"status": "ignored"}
        
        tx_data = tx.data[0]
        # Credit points
        supabase.rpc("add_points", {"user_id": tx_data["user_id"], "points": tx_data["points_added"]}).execute()
        supabase.table("transactions").update({"status": "completed"}).eq("reference", ref).execute()
    
    return {"status": "ok"}

# --- MAIN VIBE ENDPOINT ---
@app.post("/vibe")
async def vibe(prompt: Prompt):
    # Check points
    profile = supabase.table("profiles").select("points").eq("id", prompt.user_id).execute()
    if not profile.data or profile.data[0]["points"] < 1:
        return {"error": "Insufficient points. Upgrade your plan."}
    
    # Deduct 1 point
    supabase.rpc("deduct_point", {"user_id": prompt.user_id}).execute()
    
    # Get history
    history = supabase.table("messages").select("*").eq("user_id", prompt.user_id).eq("project_id", prompt.project_id).order("created_at", desc=True).limit(10).execute()
    
    # Get project
    if prompt.project_id:
        project = supabase.table("projects").select("*").eq("id", prompt.project_id).execute()
    else:
        project = None
        new_proj = supabase.table("projects").insert({
            "user_id": prompt.user_id,
            "name": f"Project {int(time.time())}",
            "points_used": 1
        }).execute()
        prompt.project_id = new_proj.data[0]["id"]
    
    # Build system prompt
    system = f"""You are VibeCode AI. You build web apps from natural language.
    User: {prompt.user_id}
    Project: {project}
    You have SQL access via Supabase. Generate code in markdown blocks.
    """
    messages = [{"role": "system", "content": system}]
    for h in history.data:
        messages.append({"role": "user" if h["sender"] == "user" else "assistant", "content": h["content"]})
    messages.append({"role": "user", "content": prompt.message})
    
    # Call OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )
    ai_reply = response.choices[0].message.content
    
    # Save message
    supabase.table("messages").insert({
        "user_id": prompt.user_id,
        "project_id": prompt.project_id,
        "sender": "assistant",
        "content": ai_reply
    }).execute()
    
    # Extract and run SQL
    sql_blocks = re.findall(r"```sql\n(.*?)\n```", ai_reply, re.DOTALL)
    for sql in sql_blocks:
        try:
            supabase.rpc("execute_sql", {"query": sql}).execute()
        except Exception as e:
            print(f"SQL error: {e}")
    
    remaining = supabase.table("profiles").select("points").eq("id", prompt.user_id).execute()
    return {
        "reply": ai_reply,
        "remaining_points": remaining.data[0]["points"] if remaining.data else 0,
        "project_id": prompt.project_id
}
    @app.get("/")
async def root():
    return {"message": "VibeCode AI Backend is running"}
