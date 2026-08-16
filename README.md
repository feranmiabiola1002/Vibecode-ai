# VibeCode AI

AI that builds web apps from natural language with point-based billing via Paystack.

## Setup
1. Copy `.env.example` to `.env` and fill in values
2. Run Supabase SQL from `schema.sql`
3. Backend: `pip install -r requirements.txt && uvicorn main:app --reload`
4. Frontend: `npm install && npm start`

## Deploy
- Backend: Render.com
- Frontend: Vercel/Netlify
