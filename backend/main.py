#!/usr/bin/env python3
# OpenClaw-Style Portfolio Agent (moved to backend/)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from fastapi import Body, HTTPException
import pathlib
import os
import json
import time

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    import yfinance as yf
except ImportError:
    yf = None

# =============================
# CONFIG
# =============================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# =============================
# MOCK DATA (replace with DB later)
# =============================
portfolio_db = {
    "stocks": [
        {"ticker": "AAPL", "cost_basis": 50000, "quantity": 200},
        {"ticker": "TSLA", "cost_basis": 30000, "quantity": 75},
        {"ticker": "MSFT", "cost_basis": 20000, "quantity": 50},
    ]
}

# persist portfolio to JSON file so it can be managed via API/UI
PORTFOLIO_FILE = os.path.join(os.path.dirname(__file__), "portfolio.json")


def save_portfolio_to_file():
    try:
        with open(PORTFOLIO_FILE, "w") as f:
            json.dump(portfolio_db, f, indent=2)
    except Exception:
        pass


def load_portfolio_from_file():
    global portfolio_db
    try:
        if os.path.exists(PORTFOLIO_FILE):
            with open(PORTFOLIO_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict) and "stocks" in data:
                    portfolio_db = data
        else:
            save_portfolio_to_file()
    except Exception:
        # keep in-memory default on error
        pass


# initialize from disk if present
load_portfolio_from_file()


# =============================
# TOOLS
# =============================

def get_portfolio():
    return portfolio_db


def analyze_stock(ticker):
    # Try to fetch real market data via yfinance. If unavailable, fall back to dummy.
    try:
        import yfinance as yf  # local import for safety
        tk = yf.Ticker(ticker)
        hist = tk.history(period="90d")
        closes = hist.get("Close")
        if closes is None:
            raise ValueError("no close prices")
        closes = closes.dropna()

        if len(closes) < 2:
            raise ValueError("not enough data")

        trend_pct = (float(closes.iloc[-1]) - float(closes.iloc[0])) / float(closes.iloc[0])
        returns = closes.pct_change().dropna()
        volatility = float(returns.std()) if len(returns) > 0 else 0.0

        if trend_pct > 0.05 and volatility < 0.05:
            recommendation = "buy"
        elif trend_pct < -0.05 and volatility > 0.07:
            recommendation = "sell"
        else:
            recommendation = "hold"

        return {
            "ticker": ticker,
            "last_price": float(closes.iloc[-1]),
            "trend_pct": round(trend_pct, 4),
            "volatility": round(volatility, 4),
            "recommendation": recommendation,
        }
    except Exception:
        return {"ticker": ticker, "recommendation": "hold"}


def rebalance_portfolio():
    return {"AAPL": 0.4, "TSLA": 0.3, "MSFT": 0.3}


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
# LLM (OpenAI) INTEGRATION
# =============================

SYSTEM_PROMPT = (
    "You are a portfolio management assistant.\n"
    "Given a user goal and tool execution context, decide the next step.\n"
    "Return a single JSON object with the keys: 'thought', 'action', 'action_input'.\n"
    "Valid actions: get_portfolio, analyze_stock, rebalance_portfolio, execute_trade, finish.\n"
    "Only return JSON — do not add extra explanation text.\n"
)


def llm_call(goal, context):
    """Call OpenAI chat completion to decide next action.

    Falls back to a small rule-based mock when OpenAI isn't available or no API key.
    """
    # Fallback to mock if no OpenAI client or API key
    if OpenAI is None or not OPENAI_API_KEY:
        if not context:
            return {"thought": "Need to see portfolio", "action": "get_portfolio", "action_input": None}
        if len(context) == 1:
            return {"thought": "Rebalance portfolio", "action": "rebalance_portfolio", "action_input": None}
        return {"thought": "Done", "action": "finish", "action_input": "Portfolio optimized"}

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Goal:\n{goal}"},
            {"role": "assistant", "content": json.dumps(context)},
        ]

        resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.2, max_tokens=512)

        content = resp.choices[0].message.content
        try:
            return json.loads(content)
        except Exception:
            import re

            m = re.search(r"\{.*\}", content, re.S)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass

        return {"thought": "LLM returned unparsable output", "action": "finish", "action_input": content}

    except Exception as e:
        return {"thought": f"OpenAI request failed: {str(e)}", "action": "finish", "action_input": "error"}


# =============================
# AGENT LOOP
# =============================


def run_agent(goal, max_steps: int = 20, max_seconds: int = 30):
    """Run the agent loop with safe limits.

    - `max_steps` limits the number of tool executions (default 20).
    - `max_seconds` limits wall-clock time for the run (default 30s).
    Returns a result with steps collected so far if a limit is reached.
    """
    context = []
    start = time.time()
    steps = 0

    while True:
        if steps >= max_steps:
            duration = time.time() - start
            # find last portfolio snapshot in context
            last_portfolio = None
            for i in range(len(context) - 1, -1, -1):
                if context[i].get("action") == "get_portfolio":
                    last_portfolio = context[i].get("result")
                    break
            return {"result": {"thought": "max_steps_reached", "action": "finish", "action_input": "max_steps"}, "last_portfolio": last_portfolio, "duration_seconds": duration}
        if time.time() - start > max_seconds:
            duration = time.time() - start
            last_portfolio = None
            for i in range(len(context) - 1, -1, -1):
                if context[i].get("action") == "get_portfolio":
                    last_portfolio = context[i].get("result")
                    break
            return {"result": {"thought": "max_time_exceeded", "action": "finish", "action_input": "timeout"}, "last_portfolio": last_portfolio, "duration_seconds": duration}

        response = llm_call(goal, context)
        action = response.get("action")
        input_data = response.get("action_input")

        if action == "finish":
            duration = time.time() - start
            last_portfolio = None
            for i in range(len(context) - 1, -1, -1):
                if context[i].get("action") == "get_portfolio":
                    last_portfolio = context[i].get("result")
                    break
            return {"result": response, "last_portfolio": last_portfolio, "duration_seconds": duration}

        result = execute_tool(action, input_data)

        # record the tool execution
        context.append({"action": action, "result": result})
        steps += 1

        # If we just retrieved the portfolio, enrich context by analyzing each holding
        if action == "get_portfolio" and isinstance(result, dict):
            stocks = result.get("stocks") or []
            analyses = []
            for s in stocks:
                ticker = s.get("ticker")
                if not ticker:
                    continue
                analysis = execute_tool("analyze_stock", ticker)
                analyses.append({"ticker": ticker, "analysis": analysis})
                context.append({"action": "analyze_stock", "ticker": ticker, "result": analysis})
                steps += 1

            # attach analyses summary to the most recent portfolio step for convenience
            for i in range(len(context) - 1, -1, -1):
                if context[i].get("action") == "get_portfolio":
                    context[i]["result"]["analyses"] = analyses
                    break


# =============================
# FASTAPI APP
# =============================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    goal: str
    max_steps: Optional[int] = 20
    max_seconds: Optional[int] = 30


@app.post("/agent/run")
def run_agent_api(req: AgentRequest):
    """Run the agent with optional per-call overrides for limits.

    Returns the agent result plus per-step logs and the run duration.
    """
    out = run_agent(req.goal, max_steps=req.max_steps or 20, max_seconds=req.max_seconds or 30)
    return out


@app.get("/")
def root():
    return {"message": "OpenClaw-style agent running"}


@app.get("/portfolio/analyze")
def portfolio_analyze():
    portfolio = get_portfolio()
    stocks = portfolio.get("stocks", []) if isinstance(portfolio, dict) else []
    analyses = []
    for s in stocks:
        ticker = s.get("ticker") if isinstance(s, dict) else None
        if not ticker:
            continue
        analysis = analyze_stock(ticker)
        analyses.append({"ticker": ticker, "analysis": analysis})
    return {"portfolio": portfolio, "analyses": analyses}


@app.get("/portfolio")
def portfolio_get():
    return {"portfolio": get_portfolio()}


@app.post("/portfolio")
def portfolio_replace(payload: dict = Body(...)):
    if not isinstance(payload, dict) or "stocks" not in payload:
        raise HTTPException(status_code=400, detail="payload must include 'stocks'")
    portfolio_db.clear()
    portfolio_db.update(payload)
    save_portfolio_to_file()
    return {"portfolio": portfolio_db}


@app.post("/portfolio/stock")
def portfolio_upsert(stock: dict = Body(...)):
    if not stock or not stock.get("ticker"):
        raise HTTPException(status_code=400, detail="stock with 'ticker' required")
    stocks = portfolio_db.get("stocks", [])
    found = False
    for s in stocks:
        if s.get("ticker") == stock.get("ticker"):
            s.update(stock)
            found = True
            break
    if not found:
        stocks.append(stock)
    portfolio_db["stocks"] = stocks
    save_portfolio_to_file()
    return {"portfolio": portfolio_db}


@app.delete("/portfolio/stock/{ticker}")
def portfolio_delete(ticker: str):
    stocks = portfolio_db.get("stocks", [])
    new = [s for s in stocks if s.get("ticker") != ticker]
    portfolio_db["stocks"] = new
    save_portfolio_to_file()
    return {"portfolio": portfolio_db}


if __name__ == "__main__":
    print("Run via: uvicorn backend.main:app --reload --port 8001")
