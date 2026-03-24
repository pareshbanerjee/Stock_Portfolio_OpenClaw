import React, { useEffect, useState } from 'react'

export default function App() {
  // Use Vite environment variable for API base so frontend works when deployed.
  // In Vercel, set VITE_API_BASE to the backend URL OR leave unset to use the built-in serverless `/api` routes.
  const API_BASE = (import.meta && import.meta.env)
    ? (import.meta.env.VITE_API_BASE || (import.meta.env.DEV ? 'http://127.0.0.1:8001' : '/api'))
    : '/api'
  const [msg, setMsg] = useState('Connecting...')
  const [runningAgent, setRunningAgent] = useState(false)
  const [runningAnalyze, setRunningAnalyze] = useState(false)
  const [result, setResult] = useState(null)
  const [analyses, setAnalyses] = useState(null)
  const [maxSteps, setMaxSteps] = useState(20)
  const [maxSeconds, setMaxSeconds] = useState(30)
  const [portfolio, setPortfolio] = useState(null)
  const [newTicker, setNewTicker] = useState('')
  const [newQuantity, setNewQuantity] = useState(0)
  const [newCostBasis, setNewCostBasis] = useState(0)
  const [editingTicker, setEditingTicker] = useState(null)
  const [currentEdit, setCurrentEdit] = useState({ quantity: 0, cost_basis: 0 })

  useEffect(() => {
    fetch(`${API_BASE}/`)
      .then((r) => r.json())
      .then((d) => setMsg(d.message))
      .catch((err) => {
        console.error('Backend root fetch failed:', err)
        setMsg('Backend not reachable')
      })

    // load portfolio for management UI using the shared helper
    refreshPortfolio()
  }, [])

  async function refreshPortfolio() {
    try {
      const res = await fetch(`${API_BASE}/portfolio`)
      const json = await res.json()
      setPortfolio(json.portfolio)
    } catch (e) {
      setPortfolio(null)
    }
  }

  async function upsertStock(stock) {
    try {
      const res = await fetch(`${API_BASE}/portfolio/stock`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(stock)
      })
      const json = await res.json()
      setPortfolio(json.portfolio)
    } catch (e) {
      console.error(e)
    }
  }

  async function deleteStock(ticker) {
    try {
      const res = await fetch(`${API_BASE}/portfolio/stock/${ticker}`, { method: 'DELETE' })
      const json = await res.json()
      setPortfolio(json.portfolio)
    } catch (e) {
      console.error(e)
    }
  }

  async function addNewStock() {
    const stock = { ticker: newTicker.toUpperCase(), quantity: Number(newQuantity), cost_basis: Number(newCostBasis) }
    await upsertStock(stock)
    setNewTicker('')
    setNewQuantity(0)
    setNewCostBasis(0)
  }

  async function runAgent() {
    setRunningAgent(true)
    setResult(null)
    try {
      const res = await fetch(`${API_BASE}/agent/run`, {
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
      const res = await fetch(`${API_BASE}/portfolio/analyze`)
      const json = await res.json()
      setAnalyses(json)
    } catch (e) {
      setAnalyses({ error: e.message })
    }
    finally {
      setRunningAnalyze(false)
    }
  }

  function formatCurrency(amount) {
    return `$${Number(amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  return (
    <div className="container">
      <h1>SmartFolio</h1>
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

      <h2>Manage Portfolio</h2>
      {portfolio ? (
        <div className="table-responsive">
          <table className="analysis-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Quantity</th>
                <th>Cost Basis</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(portfolio.stocks || []).map((s) => (
                <tr key={s.ticker}>
                  <td className="ticker-col" data-label="Ticker">{s.ticker}</td>
                  <td data-label="Quantity">
                    {editingTicker === s.ticker ? (
                      <input type="number" value={currentEdit.quantity} onChange={(e) => setCurrentEdit({ ...currentEdit, quantity: e.target.value })} style={{ width: 120 }} />
                    ) : (
                      <span>{s.quantity !== undefined ? s.quantity : '-'}</span>
                    )}
                  </td>
                  <td data-label="Cost Basis">
                    {editingTicker === s.ticker ? (
                      <input type="number" value={currentEdit.cost_basis} onChange={(e) => setCurrentEdit({ ...currentEdit, cost_basis: e.target.value })} style={{ width: 140 }} />
                    ) : (
                      <span>{s.cost_basis !== undefined ? `$${Number(s.cost_basis).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : '-'}</span>
                    )}
                  </td>
                  <td data-label="Actions">
                    {editingTicker === s.ticker ? (
                      <>
                        <button className="small-btn" onClick={async () => { await upsertStock({ ticker: s.ticker, quantity: Number(currentEdit.quantity), cost_basis: Number(currentEdit.cost_basis) }); setEditingTicker(null); }}>Save</button>
                        <button className="small-btn" style={{ marginLeft: 8 }} onClick={() => { setEditingTicker(null); setCurrentEdit({ quantity: 0, cost_basis: 0 }); }}>Cancel</button>
                      </>
                    ) : (
                      <>
                        <button className="small-btn" onClick={() => { setEditingTicker(s.ticker); setCurrentEdit({ quantity: s.quantity || 0, cost_basis: s.cost_basis || 0 }); }}>Modify</button>
                        <button className="small-btn" style={{ marginLeft: 8 }} onClick={() => deleteStock(s.ticker)}>Delete</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              <tr>
                <td data-label="Ticker">
                  <input placeholder="TICKER" value={newTicker} onChange={(e) => setNewTicker(e.target.value)} />
                </td>
                <td data-label="Quantity">
                  <input type="number" value={newQuantity} onChange={(e) => setNewQuantity(e.target.value)} style={{ width: 120 }} />
                </td>
                <td data-label="Cost Basis">
                  <input type="number" value={newCostBasis} onChange={(e) => setNewCostBasis(e.target.value)} style={{ width: 140 }} />
                </td>
                <td data-label="Actions">
                  <button onClick={addNewStock}>Add</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      ) : (
        <div>No portfolio loaded</div>
      )}
      <h2>Portfolio Analysis(LLM Agent)</h2>
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
                  <div className="summary"><strong>Portfolio Value (Current):</strong>{' '}
                  {(() => {
                    if (!portfolio.stocks) return 'n/a'
                    const val = portfolio.stocks.reduce((acc, s) => {
                      // compute position value: prefer explicit value, otherwise quantity * last_price
                          const stockAnalysis = analyses.find(r => r.ticker === s.ticker) || {}
                          const lastPrice = stockAnalysis.analysis && stockAnalysis.analysis.last_price
                          if (s.quantity !== undefined && lastPrice !== undefined) return acc + (s.quantity * lastPrice)
                          if (s.cost_basis !== undefined) return acc + Number(s.cost_basis)
                      return acc
                    }, 0)
                    return formatCurrency(val)
                  })()}
                </div>

                <div className="table-responsive">
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
                              <td data-label="Ticker">{row.ticker}</td>
                              <td data-label="Last Price">{a.last_price !== undefined ? a.last_price.toFixed(2) : '-'}</td>
                              <td data-label="Quantity">{stockEntry.quantity !== undefined ? stockEntry.quantity : '-'}</td>
                              <td data-label="Cost Basis">{stockEntry.cost_basis !== undefined ? `$${Number(stockEntry.cost_basis).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : '-'}</td>
                          {(() => {
                            const lastPrice = a.last_price
                            const posVal = (stockEntry.quantity !== undefined && lastPrice !== undefined)
                              ? stockEntry.quantity * lastPrice
                              : (stockEntry.cost_basis !== undefined ? stockEntry.cost_basis : undefined)
                            return (
                                  <td data-label="Position Value">{posVal !== undefined ? `$${Number(posVal).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : '-'}</td>
                            )
                          })()}
                          <td data-label="Trend %" className={a.trend_pct !== undefined && a.trend_pct < 0 ? 'negative' : ''}>{a.trend_pct !== undefined ? (a.trend_pct * 100).toFixed(2) + '%' : '-'}</td>
                          <td data-label="Volatility">{a.volatility !== undefined ? a.volatility.toFixed(4) : '-'}</td>
                          <td data-label="Recommendation" className={"rec-" + ((a.recommendation || 'unknown').toString().toLowerCase())}>{a.recommendation || '-'}</td>
                        </tr>
                      )
                    }) : (
                      <tr><td colSpan={8}>No analysis available</td></tr>
                    )}
                  </tbody>
                  {/* Totals row */}
                  {analyses.length > 0 && (() => {
                    const totals = analyses.reduce((acc, row) => {
                      const a = row.analysis || {}
                      const stockEntry = (portfolio.stocks || []).find(s => s.ticker === row.ticker) || {}
                      const lastPrice = a.last_price
                      const posVal = (stockEntry.quantity !== undefined && lastPrice !== undefined)
                        ? stockEntry.quantity * lastPrice
                        : (stockEntry.cost_basis !== undefined ? stockEntry.cost_basis : 0)
                      acc.cost_basis += stockEntry.cost_basis !== undefined ? Number(stockEntry.cost_basis) : 0
                      acc.position += posVal !== undefined ? Number(posVal) : 0
                      return acc
                    }, { cost_basis: 0, position: 0 })

                    return (
                      <tfoot>
                        <tr className="totals-row">
                          <td style={{ fontWeight: 800 }}>TOTAL</td>
                          <td></td>
                          <td></td>
                          <td style={{ fontWeight: 700 }}>{`$${Number(totals.cost_basis).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}</td>
                          <td style={{ fontWeight: 700 }}>{`$${Number(totals.position).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}</td>
                          <td></td>
                          <td></td>
                          <td></td>
                        </tr>
                      </tfoot>
                    )
                  })()}
                </table>
                </div>
              </div>
            )
          })()}

          <div className="summary">Duration: {result.duration_seconds ? result.duration_seconds.toFixed(2) + 's' : 'n/a'}</div>

          {/* Step logs removed from UI per user request */}
        </div>
      )}

      {!result && <div>No result yet</div>}

      <h2>Portfolio Analysis (YFinance)</h2>
      {analyses && analyses.error && (
        <div className="error">Error: {analyses.error}</div>
      )}

      {analyses && !analyses.error && (
        <div>
            <div className="summary">
            <strong>Portfolio Value (Current):</strong>{' '}
            {(() => {
              const p = analyses.portfolio
              const an = analyses.analyses || []
              if (!p || !p.stocks) return 'n/a'
              const val = p.stocks.reduce((acc, s) => {
                const a = an.find(r => r.ticker === s.ticker) || {}
                const lastPrice = a.analysis && a.analysis.last_price
                if (s.quantity !== undefined && lastPrice !== undefined) return acc + (s.quantity * lastPrice)
                if (s.cost_basis !== undefined) return acc + Number(s.cost_basis)
                return acc
              }, 0)
              return formatCurrency(val)
            })()}
          </div>

          <div className="table-responsive">
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
                      <td data-label="Ticker">{row.ticker}</td>
                      <td data-label="Last Price">{a.last_price !== undefined ? a.last_price.toFixed(2) : '-'}</td>
                      <td data-label="Quantity">{stockEntry.quantity !== undefined ? stockEntry.quantity : '-'}</td>
                      <td data-label="Cost Basis">{stockEntry.cost_basis !== undefined ? `$${Number(stockEntry.cost_basis).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : '-'}</td>
                      {(() => {
                        const lastPrice = a.last_price
                        const posVal = (stockEntry.quantity !== undefined && lastPrice !== undefined)
                          ? stockEntry.quantity * lastPrice
                          : (stockEntry.cost_basis !== undefined ? stockEntry.cost_basis : undefined)
                        return (
                          <td data-label="Position Value">{posVal !== undefined ? `$${Number(posVal).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : '-'}</td>
                        )
                      })()}
                      <td data-label="Trend %" className={a.trend_pct !== undefined && a.trend_pct < 0 ? 'negative' : ''}>{a.trend_pct !== undefined ? (a.trend_pct * 100).toFixed(2) + '%' : '-'}</td>
                      <td data-label="Volatility">{a.volatility !== undefined ? a.volatility.toFixed(4) : '-'}</td>
                      <td data-label="Recommendation" className={"rec-" + ((a.recommendation || 'unknown').toString().toLowerCase())}>{a.recommendation || '-'}</td>
                  </tr>
                )
              })}
            </tbody>
            {/* Totals for portfolio analyses */}
            {analyses.analyses && analyses.analyses.length > 0 && (() => {
              const totals = analyses.analyses.reduce((acc, row) => {
                const a = row.analysis || {}
                const stockEntry = (analyses.portfolio && analyses.portfolio.stocks || []).find(s => s.ticker === row.ticker) || {}
                const lastPrice = a.last_price
                const posVal = (stockEntry.quantity !== undefined && lastPrice !== undefined)
                  ? stockEntry.quantity * lastPrice
                  : (stockEntry.cost_basis !== undefined ? stockEntry.cost_basis : 0)
                acc.cost_basis += stockEntry.cost_basis !== undefined ? Number(stockEntry.cost_basis) : 0
                acc.position += posVal !== undefined ? Number(posVal) : 0
                return acc
              }, { cost_basis: 0, position: 0 })

              return (
                <tfoot>
                  <tr className="totals-row">
                    <td style={{ fontWeight: 800 }}>TOTAL</td>
                    <td></td>
                    <td></td>
                    <td style={{ fontWeight: 700 }}>{`$${Number(totals.cost_basis).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}</td>
                    <td style={{ fontWeight: 700 }}>{`$${Number(totals.position).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}</td>
                    <td></td>
                    <td></td>
                    <td></td>
                  </tr>
                </tfoot>
              )
            })()}
          </table>
          </div>
        </div>
      )}

      {!analyses && <div>No analysis yet</div>}
    </div>
  )
}
