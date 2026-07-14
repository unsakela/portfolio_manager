import React, { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid, XAxis, YAxis } from 'recharts';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://127.0.0.1:8000';
const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
const DEFAULT_HOLDINGS = [
  { ticker: 'RELIANCE.NS', quantity: 10, sector: 'Energy' },
  { ticker: '^NSEI', quantity: 1, sector: 'Index' },
];

async function apiPost(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail || errBody.message || `Request failed (HTTP ${res.status})`);
  }
  const data = await res.json();
  if (data?.status === 'error') throw new Error(data.message || 'Unknown error');
  return data;
}

function App() {
  const [holdings, setHoldings] = useState(DEFAULT_HOLDINGS);
  const [assetTicker, setAssetTicker] = useState('RELIANCE.NS');
  const [benchmarkTicker, setBenchmarkTicker] = useState('^NSEI');
  const [mcTicker, setMcTicker] = useState('RELIANCE.NS');
  const [horizonDays, setHorizonDays] = useState(30);
  const [nPaths, setNPaths] = useState(200);
  const [allocation, setAllocation] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [mcResult, setMcResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('darkMode') === 'true');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]);

  const runAnalysis = async () => {
    setLoading(true);
    setError('');

    try {
      const validHoldings = holdings
        .filter((item) => item.ticker.trim())
        .map((item) => ({ ticker: item.ticker.trim(), quantity: Number(item.quantity) || 0, sector: item.sector?.trim() || '' }));

      if (!validHoldings.length) {
        throw new Error('Add at least one holding to analyze.');
      }

      const parsedHorizon = Number(horizonDays);
      const parsedPaths = Number(nPaths);
      if (!Number.isFinite(parsedHorizon) || parsedHorizon < 1) throw new Error('Horizon days must be at least 1.');
      if (!Number.isFinite(parsedPaths) || parsedPaths < 10) throw new Error('Number of paths must be at least 10.');

      const sectorMap = Object.fromEntries(
        validHoldings.filter((h) => h.sector).map((h) => [h.ticker, h.sector])
      );

      const allocJson = await apiPost(`${API_BASE}/allocation`, {
        holdings: validHoldings.map(({ ticker, quantity }) => ({ ticker, quantity })),
        sector_map: sectorMap,
      });
      setAllocation(allocJson);

      const metricsJson = await apiPost(`${API_BASE}/metrics`, {
        asset_ticker: assetTicker,
        benchmark_ticker: benchmarkTicker,
      });
      setMetrics(metricsJson);

      const mcJson = await apiPost(`${API_BASE}/simulation/gbm`, {
        ticker: mcTicker,
        horizon_days: parsedHorizon,
        n_paths: parsedPaths,
        seed: 42,
      });
      setMcResult(mcJson);
    } catch (err) {
      setError(err.message || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runAnalysis();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateHolding = (index, field, value) => {
    setHoldings(holdings.map((item, i) => (i === index ? { ...item, [field]: value } : item)));
  };

  const addHolding = () => {
    setHoldings([...holdings, { ticker: '', quantity: 1, sector: '' }]);
  };

  const removeHolding = (index) => {
    const updated = holdings.filter((_, itemIndex) => itemIndex !== index);
    setHoldings(updated);
  };

  const allocationData = allocation?.by_sector?.map((item) => ({ name: item.sector, value: item.market_value })) || [];
  const chartData = Array.from({ length: Number(horizonDays) }, (_, index) => {
    const point = { day: index + 1 };
    const paths = mcResult?.simulated_paths || [];
    paths.slice(0, 5).forEach((path, pathIndex) => {
      point[`path${pathIndex + 1}`] = path[index];
    });
    return point;
  });

  return (
    <div className="app-shell">
      <div className="hero-card">
        <div>
          <p className="eyebrow">Historical-only portfolio analytics</p>
          <h1>Portfolio Risk Analytics</h1>
          <p className="hero-copy">Explore holdings, allocation mix, risk metrics, and Monte Carlo stress outcomes from your local cache.</p>
        </div>
        <div className="hero-actions">
          <button className="primary-btn" onClick={runAnalysis}>
            {loading ? 'Analyzing…' : 'Run analysis'}
          </button>
          <button className="toggle-btn" onClick={() => setDarkMode((d) => !d)}>
            {darkMode ? 'Light mode' : 'Dark mode'}
          </button>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="control-grid">
        <section className="panel">
          <h2>Portfolio holdings</h2>
          <div className="holdings-list">
            {holdings.map((item, index) => (
              <div className="holding-row" key={index}>
                <input
                  value={item.ticker}
                  placeholder="Ticker"
                  onChange={(event) => updateHolding(index, 'ticker', event.target.value)}
                />
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  value={item.quantity}
                  onChange={(event) => updateHolding(index, 'quantity', event.target.value)}
                />
                <input
                  value={item.sector || ''}
                  placeholder="Sector"
                  onChange={(event) => updateHolding(index, 'sector', event.target.value)}
                />
                <button className="ghost-btn" onClick={() => removeHolding(index)}>
                  Remove
                </button>
              </div>
            ))}
          </div>
          <button className="secondary-btn" onClick={addHolding}>
            + Add holding
          </button>
        </section>

        <section className="panel">
          <h2>Analysis settings</h2>
          <label>
            Asset ticker
            <input value={assetTicker} onChange={(event) => setAssetTicker(event.target.value)} />
          </label>
          <label>
            Benchmark ticker
            <input value={benchmarkTicker} onChange={(event) => setBenchmarkTicker(event.target.value)} />
          </label>
          <label>
            Monte Carlo ticker
            <input value={mcTicker} onChange={(event) => setMcTicker(event.target.value)} />
          </label>
          <div className="inline-fields">
            <label>
              Horizon (days)
              <input type="number" min="1" value={horizonDays} onChange={(event) => setHorizonDays(event.target.value)} />
            </label>
            <label>
              Paths
              <input type="number" min="10" value={nPaths} onChange={(event) => setNPaths(event.target.value)} />
            </label>
          </div>
        </section>
      </div>

      {loading ? (
        <div className="panel loading-panel">Loading analytics…</div>
      ) : (
        <>
          <section className="panel">
            <div className="section-title-row">
              <h2>Portfolio allocation</h2>
              <div className="pill">Total value: {allocation?.total_value?.toLocaleString() || '—'}</div>
            </div>
            <div className="stats-grid">
              <div className="chart-card">
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie data={allocationData} dataKey="value" nameKey="name" outerRadius={90}>
                      {allocationData.map((entry, index) => (
                        <Cell key={`cell-${entry.name}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="table-card">
                <h3>By stock</h3>
                <table>
                  <thead>
                    <tr>
                      <th>Ticker</th>
                      <th>Weight</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allocation?.by_stock?.map((item) => (
                      <tr key={item.ticker}>
                        <td>{item.ticker}</td>
                        <td>{item.allocation_pct}%</td>
                        <td>{item.market_value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <section className="panel">
            <h2>Risk metrics</h2>
            <div className="metric-grid">
              <div className="metric-card">
                <span>Beta</span>
                <strong>{metrics?.beta ?? '—'}</strong>
              </div>
              <div className="metric-card">
                <span>Alpha</span>
                <strong>{metrics?.alpha ?? '—'}</strong>
              </div>
              <div className="metric-card">
                <span>Sharpe</span>
                <strong>{metrics?.sharpe_ratio ?? '—'}</strong>
              </div>
              <div className="metric-card">
                <span>Max drawdown</span>
                <strong>{metrics?.max_drawdown_pct ?? '—'}%</strong>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="section-title-row">
              <h2>Monte Carlo outlook</h2>
              <div className="pill">VaR 95%: {mcResult?.var_95 ?? '—'}</div>
            </div>
            <p className="muted">Breach probability: {mcResult?.breach_probability ?? '—'}</p>
            <div className="chart-card wide">
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={chartData}>
                  <CartesianGrid stroke={darkMode ? '#334155' : '#e2e8f0'} strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  {mcResult?.simulated_paths?.slice(0, 5).map((_, index) => (
                    <Line key={`path-${index}`} type="monotone" dataKey={`path${index + 1}`} stroke={COLORS[index % COLORS.length]} dot={false} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

export default App;
