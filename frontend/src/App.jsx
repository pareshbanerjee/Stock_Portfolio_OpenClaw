import React, { useEffect, useState } from 'react'

export default function App() {
  const [msg, setMsg] = useState('Connecting...')
  const [runningAgent, setRunningAgent] = useState(false)
  const [runningAnalyze, setRunningAnalyze] = useState(false)
  const [result, setResult] = useState(null)
  const [analyses, setAnalyses] = useState(null)
  const [maxSteps, setMaxSteps] = useState(20)
  const [maxSeconds, setMaxSeconds] = useState(30)

  useEffect(() => {
    fetch('http://localhost:8001/')
      .then((r) => r.json())
      .then((d) => setMsg(d.message))
      .catch(() => setMsg('Backend not reachable'))
  }, [])

  async function runAgent() {
    setRunningAgent(true)
    setResult(null)
    try {
      const res = await fetch('http://localhost:8001/agent/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: 'Optimize portfolio', max_steps: maxSteps, max_seconds: maxSeconds })
      })
      const json = await res.json()
      setResult(json)
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setRunningAgent(false)
    }
  }

  async function analyzePortfolio() {
    setAnalyses(null)
    setRunningAnalyze(true)
    try {
      const res = await fetch('http://localhost:8001/portfolio/analyze')
      const json = await res.json()
      setAnalyses(json)
    } catch (e) {
      setAnalyses({ error: e.message })
    }
    finally {
      setRunningAnalyze(false)
    }
  }

  return (
    <div className="container">
      <h1>OpenClaw Portfolio Dashboard</h1>
      <p>{msg}</p>
      <div className="controls">
        <button onClick={runAgent} disabled={runningAgent}>{runningAgent ? 'Running...' : 'Analyze Portfolio(LLM)'}</button>
        <button onClick={analyzePortfolio} style={{ marginLeft: 12 }} disabled={runningAnalyze || runningAgent}>{runningAnalyze ? 'Running...' : 'Analyze Portfolio(YFinance)'}</button>

        <label style={{ marginLeft: 12, display: 'inline-flex', alignItems: 'center' }}>
          Max Steps:&nbsp;
          <input type="number" min={1} value={maxSteps} onChange={(e) => setMaxSteps(Number(e.target.value) || 1)} style={{ width: 80 }} />
        </label>

        <label style={{ marginLeft: 12, display: 'inline-flex', alignItems: 'center' }}>
          Max Secs:&nbsp;
          <input type="number" min={1} value={maxSeconds} onChange={(e) => setMaxSeconds(Number(e.target.value) || 1)} style={{ width: 80 }} />
        </label>
      </div>
      <h2>Agent Result</h2>
      {result && result.error && (
        <div className="error">Error: {result.error}</div>
      )}

      {result && !result.error && (
        <div>
          <div className="summary"><strong>Goal:</strong> {result.goal || 'N/A'}</div>

          {/* Use the last_portfolio returned by the API (no full step logs) */}
          {(() => {
            const portfolio = result.last_portfolio || null
            if (!portfolio) {
              return <div>No portfolio data returned by agent.</div>
            }
            const analyses = portfolio.analyses || []

            return (
              <div>
                <div className="summary"><strong>Portfolio Value:</strong>{' '}
                  {(() => {
                    if (!portfolio.stocks) return 'n/a'
                    return portfolio.stocks.reduce((acc, s) => {
                      // compute position value: prefer explicit value, otherwise quantity * last_price
                      const stockAnalysis = analyses.find(r => r.ticker === s.ticker) || {}
                      const lastPrice = stockAnalysis.analysis && stockAnalysis.analysis.last_price
                      if (s.cost_basis !== undefined) return acc + Number(s.cost_basis)
                      if (s.quantity !== undefined && lastPrice !== undefined) return acc + (s.quantity * lastPrice)
                      return acc
                    }, 0)
                  })()}
                </div>

                <table className="analysis-table">
                  <thead>
                    <tr>
                      <th>Ticker</th>
                      <th>Last Price</th>
                      <th>Quantity</th>
                      <th>Cost Basis</th>
                      <th>Position Value</th>
                      <th>Trend %</th>
                      <th>Volatility</th>
                      <th>Recommendation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analyses.length > 0 ? analyses.map((row) => {
                      const a = row.analysis || {}
                      const stockEntry = (portfolio.stocks || []).find(s => s.ticker === row.ticker) || {}
                      return (
                        <tr key={row.ticker}>
                          <td>{row.ticker}</td>
                          <td>{a.last_price !== undefined ? a.last_price.toFixed(2) : '-'}</td>
                          <td>{stockEntry.quantity !== undefined ? stockEntry.quantity : '-'}</td>
                          <td>{stockEntry.cost_basis !== undefined ? `$${Number(stockEntry.cost_basis).toLocaleString()}` : '-'}</td>
                          {(() => {
                            const lastPrice = a.last_price
                            const posVal = (stockEntry.quantity !== undefined && lastPrice !== undefined)
                              ? stockEntry.quantity * lastPrice
                              : (stockEntry.cost_basis !== undefined ? stockEntry.cost_basis : undefined)
                            return (
                              <td>{posVal !== undefined ? `$${Number(posVal).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : '-'}</td>
                            )
                          })()}
                          <td>{a.trend_pct !== undefined ? (a.trend_pct * 100).toFixed(2) + '%' : '-'}</td>
                          <td>{a.volatility !== undefined ? a.volatility.toFixed(4) : '-'}</td>
                          <td>{a.recommendation || '-'}</td>
                        </tr>
                      )
                    }) : (
                      <tr><td colSpan={8}>No analyses available</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )
          })()}

          <div className="summary">Duration: {result.duration_seconds ? result.duration_seconds.toFixed(2) + 's' : 'n/a'}</div>

          {/* Step logs removed from UI per user request */}
        </div>
      )}

      {!result && <div>No result yet</div>}

      <h2>Portfolio Analyses</h2>
      {analyses && analyses.error && (
        <div className="error">Error: {analyses.error}</div>
      )}

      {analyses && !analyses.error && (
        <div>
            <div className="summary">
            <strong>Portfolio Value:</strong>{' '}
            {(() => {
              const p = analyses.portfolio
              const an = analyses.analyses || []
              if (!p || !p.stocks) return 'n/a'
              return p.stocks.reduce((acc, s) => {
                const a = an.find(r => r.ticker === s.ticker) || {}
                const lastPrice = a.analysis && a.analysis.last_price
                if (s.cost_basis !== undefined) return acc + Number(s.cost_basis)
                if (s.quantity !== undefined && lastPrice !== undefined) return acc + (s.quantity * lastPrice)
                return acc
              }, 0)
            })()}
          </div>

          <table className="analysis-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Last Price</th>
                <th>Quantity</th>
                <th>Cost Basis</th>
                <th>Position Value</th>
                <th>Trend %</th>
                <th>Volatility</th>
                <th>Recommendation</th>
              </tr>
            </thead>
            <tbody>
              {analyses.analyses && analyses.analyses.map((row) => {
                const a = row.analysis || {}
                // find value from portfolio
                const stockEntry = (analyses.portfolio && analyses.portfolio.stocks || []).find(s => s.ticker === row.ticker) || {}
                return (
                  <tr key={row.ticker}>
                      <td>{row.ticker}</td>
                      <td>{a.last_price !== undefined ? a.last_price.toFixed(2) : '-'}</td>
                      <td>{stockEntry.quantity !== undefined ? stockEntry.quantity : '-'}</td>
                      <td>{stockEntry.cost_basis !== undefined ? `$${Number(stockEntry.cost_basis).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : '-'}</td>
                      {(() => {
                        const lastPrice = a.last_price
                        const posVal = (stockEntry.quantity !== undefined && lastPrice !== undefined)
                          ? stockEntry.quantity * lastPrice
                          : (stockEntry.cost_basis !== undefined ? stockEntry.cost_basis : undefined)
                        return (
                          <td>{posVal !== undefined ? `$${Number(posVal).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : '-'}</td>
                        )
                      })()}
                      <td>{a.trend_pct !== undefined ? (a.trend_pct * 100).toFixed(2) + '%' : '-'}</td>
                      <td>{a.volatility !== undefined ? a.volatility.toFixed(4) : '-'}</td>
                      <td>{a.recommendation || '-'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {!analyses && <div>No analyses yet</div>}
    </div>
  )
}
