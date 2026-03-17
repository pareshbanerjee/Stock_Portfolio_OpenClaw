import React, { useEffect, useState } from 'react'

export default function App() {
  const [msg, setMsg] = useState('Connecting...')
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    fetch('http://localhost:8001/')
      .then((r) => r.json())
      .then((d) => setMsg(d.message))
      .catch(() => setMsg('Backend not reachable'))
  }, [])

  async function runAgent() {
    setRunning(true)
    setResult(null)
    try {
      const res = await fetch('http://localhost:8001/agent/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: 'Optimize portfolio' })
      })
      const json = await res.json()
      setResult(json)
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="container">
      <h1>OpenClaw Portfolio Dashboard</h1>
      <p>{msg}</p>
      <div className="controls">
        <button onClick={runAgent} disabled={running}>{running ? 'Running...' : 'Run Agent'}</button>
      </div>
      <h2>Agent Result</h2>
      <pre className="result">{result ? JSON.stringify(result, null, 2) : 'No result yet'}</pre>
    </div>
  )
}
