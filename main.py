# =============================
# OpenClaw-Style Portfolio Agent
# Backend: FastAPI + Simple Agent Loop
# Run: pip install fastapi uvicorn openai
# Then: uvicorn main:app --reload
# =============================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json

# Optional: load environment variables from a .env file during development
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv not installed or no .env present — that's fine in production
    pass

# =============================
# CONFIG
# =============================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    # Helpful message when running locally without the key set
    # (do not print keys or store them in code)
    pass

# =============================
# MOCK DATA (replace with DB later)
# =============================
portfolio_db = {
    "stocks": [
        {"ticker": "AAPL", "value": 50000},
        {"ticker": "TSLA", "value": 30000},
        {"ticker": "MSFT", "value": 20000}
    ]
}

# =============================
# TOOLS
# =============================

def get_portfolio():
    return portfolio_db


def analyze_stock(ticker):
    # Dummy logic (replace with real API)
    return {
        "ticker": ticker,
        "trend": "bullish",
        "risk": "medium",
        "recommendation": "hold"
    }


def rebalance_portfolio():
    return {
        "AAPL": 0.4,
        "TSLA": 0.3,
        "MSFT": 0.3
    }


def execute_trade(action):
    return {"status": "EXECUTED", "details": action}


# =============================
# TOOL EXECUTOR
# =============================

def execute_tool(action, input_data=None):
    if action == "get_portfolio":
        return get_portfolio()
    elif action == "analyze_stock":
        return analyze_stock(input_data)
    elif action == "rebalance_portfolio":
        return rebalance_portfolio()
    elif action == "execute_trade":
        return execute_trade(input_data)
    else:
        return {"error": "Unknown action"}


# =============================
# LLM CALL (mock for now)
# Replace with real OpenAI call later
# =============================

def llm_call(goal, context):
    # VERY SIMPLE RULE-BASED MOCK
    if not context:
        return {
            "thought": "Need to see portfolio",
            "action": "get_portfolio",
            "action_input": None
        }

    if len(context) == 1:
        return {
            "thought": "Rebalance portfolio",
            "action": "rebalance_portfolio",
            "action_input": None
        }

    return {
        "thought": "Done",
        "action": "finish",
        "action_input": "Portfolio optimized"
    }


# =============================
# AGENT LOOP
# =============================

def run_agent(goal):
    context = []

    while True:
        response = llm_call(goal, context)

        action = response["action"]
        input_data = response.get("action_input")

        if action == "finish":
            return {
                "result": response,
                "steps": context
            }

        result = execute_tool(action, input_data)

        context.append({
            "action": action,
            "result": result
        })


# =============================
# FASTAPI APP
# =============================

app = FastAPI()

# Allow local frontend (Vite) to access the API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    goal: str


@app.post("/agent/run")
def run_agent_api(req: AgentRequest):
    return run_agent(req.goal)


@app.get("/")
def root():
    return {"message": "OpenClaw-style agent running"}


# =============================
# OPTIONAL: REAL OPENAI INTEGRATION
# =============================

'''
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are a portfolio agent.
Return JSON with: thought, action, action_input
"""


def llm_call(goal, context):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": goal},
            {"role": "assistant", "content": json.dumps(context)}
        ]
    )

    return json.loads(response.choices[0].message.content)
'''
