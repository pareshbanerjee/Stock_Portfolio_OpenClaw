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

try:
    import numpy as np
except ImportError:
    np = None

try:
    from yfinance import Ticker
    import yfinance as yf
except ImportError:
    yf = None

# Optional: load environment variables from a .env file during development
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
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
    # Try to fetch real market data via yfinance. If unavailable, fall back to dummy.
    try:
        import yfinance as yf
        import numpy as np

        tk = yf.Ticker(ticker)
        hist = tk.history(period="90d")
        closes = hist['Close'].dropna()

        if len(closes) < 2:
            raise ValueError('not enough data')

        # Simple trend: percentage change over the window
        trend_pct = (float(closes.iloc[-1]) - float(closes.iloc[0])) / float(closes.iloc[0])

        # Volatility: std of daily returns
        returns = closes.pct_change().dropna()
        volatility = float(returns.std()) if len(returns) > 0 else 0.0

        # Basic recommendation logic
        if trend_pct > 0.05 and volatility < 0.05:
            recommendation = 'buy'
        elif trend_pct < -0.05 and volatility > 0.07:
            recommendation = 'sell'
        else:
            recommendation = 'hold'

        return {
            "ticker": ticker,
            "last_price": float(closes.iloc[-1]),
            "trend_pct": round(trend_pct, 4),
            "volatility": round(volatility, 4),
            "recommendation": recommendation
        }
    except Exception:
        # Fallback to previous dummy output if yfinance isn't installed or data missing
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

        # record the tool execution
        context.append({
            "action": action,
            "result": result
        })

        # If we just retrieved the portfolio, enrich context by analyzing
        # each holding (current value + recommendation) so the agent can
        # reason over up-to-date market information.
        if action == "get_portfolio" and isinstance(result, dict):
            stocks = result.get("stocks") or []
            analyses = []
            for s in stocks:
                ticker = s.get("ticker")
                if not ticker:
                    continue
                analysis = execute_tool("analyze_stock", ticker)
                analyses.append({"ticker": ticker, "analysis": analysis})
                # also record each analysis as a step in the context
                context.append({
                    "action": "analyze_stock",
                    "ticker": ticker,
                    "result": analysis
                })

            # attach analyses summary to the last portfolio step for convenience
            context[-(len(analyses)+1)]["result"]["analyses"] = analyses


# =============================
# FASTAPI APP
# =============================

app = FastAPI()

# Allow local frontend (Vite) to access the API during development
app.add_middleware(
    CORSMiddleware,
    # Allow common local dev origins (Vite uses localhost or network IP)
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://192.168.1.180:5173"],
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


@app.get("/portfolio/analyze")
def portfolio_analyze():
    """Return current portfolio plus per-holding analysis (price, trend, recommendation)."""
    portfolio = get_portfolio()
    stocks = portfolio.get("stocks", []) if isinstance(portfolio, dict) else []
    analyses = []
    for s in stocks:
        ticker = s.get("ticker") if isinstance(s, dict) else None
        if not ticker:
            continue
        # call analyze_stock to fetch current data / recommendation
        analysis = analyze_stock(ticker)
        analyses.append({"ticker": ticker, "analysis": analysis})

    return {"portfolio": portfolio, "analyses": analyses}


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
