import os
import json
import time

ROOT = os.path.dirname(os.path.dirname(__file__))
PORTFOLIO_FILE = os.path.join(ROOT, 'backend', 'portfolio.json')


def load_portfolio():
    try:
        with open(PORTFOLIO_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"stocks": []}


def save_portfolio(data):
    try:
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def analyze_stock_simple(ticker: str):
    """Lightweight analysis with yfinance when available; fallback to hold."""
    try:
        import yfinance as yf
        tk = yf.Ticker(ticker)
        hist = tk.history(period="90d")
        closes = hist.get('Close')
        if closes is None or len(closes.dropna()) < 2:
            return {"ticker": ticker, "recommendation": "hold"}
        closes = closes.dropna()
        trend_pct = (float(closes.iloc[-1]) - float(closes.iloc[0])) / float(closes.iloc[0])
        returns = closes.pct_change().dropna()
        volatility = float(returns.std()) if len(returns) > 0 else 0.0
        if trend_pct > 0.05 and volatility < 0.05:
            recommendation = 'buy'
        elif trend_pct < -0.05 and volatility > 0.07:
            recommendation = 'sell'
        else:
            recommendation = 'hold'
        return {
            'ticker': ticker,
            'last_price': float(closes.iloc[-1]),
            'trend_pct': round(trend_pct, 4),
            'volatility': round(volatility, 4),
            'recommendation': recommendation,
        }
    except Exception:
        return {"ticker": ticker, "recommendation": "hold"}


def run_agent_simple(goal: str, max_steps=20, max_seconds=30):
    """A minimal, synchronous agent that: get portfolio -> analyze holdings -> return summary."""
    start = time.time()
    portfolio = load_portfolio()
    stocks = portfolio.get('stocks', [])
    analyses = []
    steps = 0
    for s in stocks:
        if steps >= max_steps or (time.time() - start) > max_seconds:
            break
        ticker = s.get('ticker')
        if not ticker:
            continue
        a = analyze_stock_simple(ticker)
        analyses.append({'ticker': ticker, 'analysis': a})
        steps += 1

    duration = time.time() - start
    return {'result': {'thought': 'done', 'action': 'finish', 'action_input': 'completed'}, 'last_portfolio': {'stocks': stocks, 'analyses': analyses}, 'duration_seconds': duration}


def llm_call(goal, context):
    """Call OpenAI if available, otherwise return None to indicate no LLM present."""
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
    except Exception:
        return None

    SYSTEM_PROMPT = (
        "You are a portfolio management assistant.\n"
        "Return a single JSON object with keys: 'thought', 'action', 'action_input'.\n"
        "Valid actions: get_portfolio, analyze_stock, rebalance_portfolio, execute_trade, finish."
    )

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
        return None
    except Exception:
        return None


def run_agent(goal: str, max_steps=20, max_seconds=30):
    """Run agent using OpenAI when available, otherwise fallback to simple runner."""
    # Try LLM first
    ctx = []
    start = time.time()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if OPENAI_API_KEY:
        # run loop with llm
        steps = 0
        while True:
            if steps >= max_steps or (time.time() - start) > max_seconds:
                duration = time.time() - start
                last_portfolio = None
                for i in range(len(ctx) - 1, -1, -1):
                    if ctx[i].get('action') == 'get_portfolio':
                        last_portfolio = ctx[i].get('result')
                        break
                return {'result': {'thought': 'timeout_or_max', 'action': 'finish', 'action_input': 'timeout_or_max'}, 'last_portfolio': last_portfolio, 'duration_seconds': duration}

            resp = llm_call(goal, ctx)
            if not resp:
                break
            action = resp.get('action')
            input_data = resp.get('action_input')
            if action == 'finish':
                duration = time.time() - start
                last_portfolio = None
                for i in range(len(ctx) - 1, -1, -1):
                    if ctx[i].get('action') == 'get_portfolio':
                        last_portfolio = ctx[i].get('result')
                        break
                return {'result': resp, 'last_portfolio': last_portfolio, 'duration_seconds': duration}

            # execute action
            if action == 'get_portfolio':
                result = load_portfolio()
            elif action == 'analyze_stock':
                result = analyze_stock_simple(input_data)
            elif action == 'rebalance_portfolio':
                result = {'rebalance': 'not_implemented'}
            elif action == 'execute_trade':
                result = {'execute_trade': input_data}
            else:
                result = {'error': 'unknown action'}

            ctx.append({'action': action, 'result': result})
            steps += 1

            # if we just got portfolio, analyze holdings
            if action == 'get_portfolio' and isinstance(result, dict):
                stocks = result.get('stocks', [])
                analyses = []
                for s in stocks:
                    ticker = s.get('ticker')
                    if not ticker:
                        continue
                    a = analyze_stock_simple(ticker)
                    analyses.append({'ticker': ticker, 'analysis': a})
                    ctx.append({'action': 'analyze_stock', 'ticker': ticker, 'result': a})
                    steps += 1
                # attach analyses
                for i in range(len(ctx) - 1, -1, -1):
                    if ctx[i].get('action') == 'get_portfolio':
                        ctx[i]['result']['analyses'] = analyses
                        break

        # fallback if LLM loop ended
    # fallback to simple runner
    return run_agent_simple(goal, max_steps=max_steps, max_seconds=max_seconds)
