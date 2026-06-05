import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Adjust paths to make sure we import local modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from intent_classifier import IntentClassifier, UserIntent
from retrieval import MutualFundRetrievalEngine
from guardrails import GroqGuardrailClient

# ---------------------------------------------------------------------------
# Lifespan: initialise heavy components once on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global classifier, retrieval_engine, guardrail_client
    try:
        print("[INFO] Initialising backend components...")
        classifier = IntentClassifier()
        retrieval_engine = MutualFundRetrievalEngine()
        guardrail_client = GroqGuardrailClient()
        print("[SUCCESS] All backend components ready.")
    except Exception as e:
        print(f"[ERROR] Failed to initialise backend: {e}")
        classifier = None
        retrieval_engine = None
        guardrail_client = None
    yield  # server is running

app = FastAPI(title="Mutual Fund RAG Chatbot API", lifespan=lifespan)

# ---------------------------------------------------------------------------
# CORS — driven by env var so Vercel domain can be locked in production
# CORS_ORIGINS="https://your-project.vercel.app" in Railway Variables
# Leave unset (or "*") for local development / testing
# ---------------------------------------------------------------------------
_raw_origins = os.environ.get("CORS_ORIGINS", "*")
ALLOWED_ORIGINS: list[str] = (
    [o.strip() for o in _raw_origins.split(",") if o.strip()]
    if _raw_origins != "*"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Module-level placeholders (populated inside lifespan above)
classifier = None
retrieval_engine = None
guardrail_client = None

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    intent: str
    scheme_name: Optional[str] = None
    url: Optional[str] = None
    is_fallback: bool = False

GREETINGS = ["hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "help"]

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not classifier or not retrieval_engine or not guardrail_client:
        raise HTTPException(status_code=500, detail="Backend services are not properly initialized. Check server logs.")

    query = request.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Empty query provided.")

    # 1. Check for basic greetings first to avoid unnecessary LLM calls and give a standard friendly response
    if query.lower().replace("!", "") in GREETINGS:
        welcome_msg = (
            "Hello! I am your Mutual Fund FAQ Assistant. I can provide you with factual information about "
            "the following 5 HDFC Mutual Fund schemes:\n\n"
            "- HDFC Mid Cap Fund Direct Growth\n"
            "- HDFC Large Cap Fund Direct Growth\n"
            "- HDFC Small Cap Fund Direct Growth\n"
            "- HDFC Gold ETF Fund of Fund Direct Plan Growth\n"
            "- HDFC Defence Fund Direct Growth\n\n"
            "Feel free to ask about their NAV, expense ratio, exit load, fund managers, or investment objectives."
        )
        return ChatResponse(
            response=welcome_msg,
            intent="factual",
            scheme_name=None,
            url=None,
            is_fallback=False
        )

    # 2. Classify intent
    try:
        intent, score, matched = classifier.classify(query)
    except Exception as e:
        print(f"Error in intent classification: {e}")
        intent = UserIntent.FACTUAL # Fallback to factual so we try to retrieve info

    # 3. Handle Refusals (Advisory / Out-Of-Scope)
    if intent in [UserIntent.ADVISORY, UserIntent.OUT_OF_SCOPE]:
        refusal_msg = classifier.get_refusal_response(intent)
        return ChatResponse(
            response=refusal_msg,
            intent=intent.value,
            scheme_name=None,
            url=None,
            is_fallback=False
        )

    # 4. Handle Factual Queries (RAG Pipeline)
    try:
        scheme_name = retrieval_engine.extract_scheme_name(query)
        context, items = retrieval_engine.build_prompt_context(query)
        
        # Extract metadata from the first retrieved item or matching fund
        matched_fund = None
        if scheme_name:
            matched_fund = next((fund for fund in retrieval_engine.corpus if fund.get("scheme_name") == scheme_name), None)
        
        metrics = {}
        target_url = None
        if matched_fund:
            metrics = matched_fund
            target_url = matched_fund.get("url")
        elif items:
            # Fallback to first retrieved item metadata
            target_url = items[0]["metadata"].get("url")
            # Reconstruct basic metrics dictionary from the corpus if possible
            matched_name = items[0]["metadata"].get("scheme_name")
            matched_fund = next((fund for fund in retrieval_engine.corpus if fund.get("scheme_name") == matched_name), None)
            if matched_fund:
                metrics = matched_fund
        
        # Call Groq LLM with Guardrails
        response_text = guardrail_client.generate_response(query, context, metrics)
        
        # Check if the generated response was a template fallback
        # (Usually contains "The [scheme_name] has a Net Asset Value...")
        is_fallback = "The " in response_text and "has a Net Asset Value" in response_text
        
        return ChatResponse(
            response=response_text,
            intent="factual",
            scheme_name=scheme_name or (matched_fund.get("scheme_name") if matched_fund else None),
            url=target_url,
            is_fallback=is_fallback
        )

    except Exception as e:
        print(f"Error in RAG generation pipeline: {e}")
        # If everything fails, return a safe hardcoded error message
        return ChatResponse(
            response="I encountered an error while processing your request. Please try again or ask a simpler factual question.",
            intent="factual",
            is_fallback=True
        )

@app.get("/api/funds")
async def get_funds():
    if not retrieval_engine or not retrieval_engine.corpus:
        return []
    
    # Return basic information of the 5 funds for the sidebar UI
    funds_info = []
    for fund in retrieval_engine.corpus:
        funds_info.append({
            "name": fund.get("scheme_name"),
            "category": fund.get("category"),
            "sub_category": fund.get("sub_category"),
            "nav": fund.get("nav"),
            "nav_date": fund.get("nav_date"),
            "url": fund.get("url"),
            "aum": fund.get("aum"),
            "return_1y": fund.get("return_1y")
        })
    return funds_info

@app.get("/health")
async def health_check():
    """
    Railway health check endpoint.
    Returns 200 when all backend components are ready, 503 otherwise.
    """
    ready = all([classifier, retrieval_engine, guardrail_client])
    fund_count = len(retrieval_engine.corpus) if retrieval_engine else 0
    payload = {
        "status": "ok" if ready else "degraded",
        "components": {
            "intent_classifier": classifier is not None,
            "retrieval_engine": retrieval_engine is not None,
            "guardrail_client": guardrail_client is not None,
        },
        "funds_loaded": fund_count,
    }
    status_code = 200 if ready else 503
    return JSONResponse(content=payload, status_code=status_code)


dist_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(dist_path):
    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(dist_path, "index.html"))
        
    assets_path = os.path.join(dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
