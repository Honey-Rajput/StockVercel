"use client";
import { useState, useEffect } from "react";
import RunAnalysisButton from './components/RunAnalysisButton';


/* ========================================
   HELPER COMPONENTS
   ======================================== */
function getSignalClass(signal) {
  if (!signal) return "hold";
  const s = signal.toLowerCase();
  if (s.includes("strong buy")) return "strong-buy";
  if (s.includes("buy")) return "buy";
  if (s.includes("strong sell")) return "strong-sell";
  if (s.includes("sell")) return "sell";
  return "hold";
}

function getSignalLabel(signal) {
  if (!signal) return "Hold";
  return signal.replace(/[🟢🔵🟡🟠🔴]\s*/g, "").trim();
}

function getScoreColor(score) {
  if (score >= 80) return "#10b981";
  if (score >= 65) return "#3b82f6";
  if (score >= 50) return "#f59e0b";
  if (score >= 35) return "#f97316";
  return "#ef4444";
}

function ScoreBar({ score }) {
  const color = getScoreColor(score);
  return (
    <div className="score-bar-wrap">
      <div className="score-bar-track">
        <div
          className="score-bar-fill"
          style={{ width: `${Math.min(score, 100)}%`, background: color }}
        />
      </div>
      <span className="score-value" style={{ color }}>
        {Math.round(score)}
      </span>
    </div>
  );
}

function MetricCard({ icon, value, label, variant = "" }) {
  return (
    <div className={`metric-card ${variant}`}>
      <div className="metric-icon">{icon}</div>
      <div className={`metric-value ${variant ? "" : "gradient"}`}>{value}</div>
      <div className="metric-label">{label}</div>
    </div>
  );
}

function PickCard({ stock, rank }) {
  const change = parseFloat(stock.change_pct || 0);
  return (
    <div className="pick-card">
      <div className="pick-card-rank">#{rank}</div>
      <div className="pick-card-header">
        <div>
          <div className="pick-card-symbol">{stock.symbol}</div>
          <div className="pick-card-name">{stock.name}</div>
        </div>
      </div>
      <div style={{ marginBottom: 12 }}>
        <span className={`signal-badge ${getSignalClass(stock.signal)}`}>
          {getSignalLabel(stock.signal)}
        </span>
      </div>
      <div className="pick-card-metrics">
        <div className="pick-metric">
          <span className="pick-metric-label">Price</span>
          <span className="pick-metric-value">
            ₹{Number(stock.close).toLocaleString("en-IN")}
          </span>
        </div>
        <div className="pick-metric">
          <span className="pick-metric-label">Change</span>
          <span
            className={`pick-metric-value ${change >= 0 ? "price-green" : "price-red"}`}
          >
            {change >= 0 ? "+" : ""}
            {change.toFixed(2)}%
          </span>
        </div>
        <div className="pick-metric">
          <span className="pick-metric-label">Score</span>
          <span className="pick-metric-value price-blue">
            {Math.round(stock.composite_score || 0)}
          </span>
        </div>
        <div className="pick-metric">
          <span className="pick-metric-label">Target</span>
          <span className="pick-metric-value price-green">
            ₹{Number(stock.target_1 || 0).toLocaleString("en-IN")}
          </span>
        </div>
        <div className="pick-metric">
          <span className="pick-metric-label">Stop Loss</span>
          <span className="pick-metric-value price-red">
            ₹{Number(stock.stop_loss || 0).toLocaleString("en-IN")}
          </span>
        </div>
        <div className="pick-metric">
          <span className="pick-metric-label">RSI</span>
          <span className="pick-metric-value">{Number(stock.rsi || 0).toFixed(1)}</span>
        </div>
      </div>
    </div>
  );
}

/* ========================================
   MAIN DASHBOARD PAGE
   ======================================== */
export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("intraday");
  const [data, setData] = useState({});
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterSignal, setFilterSignal] = useState("All");
  const [filterSector, setFilterSector] = useState("All");
  const [searchQuery, setSearchQuery] = useState("");

  const timeframes = [
    { key: "intraday", label: "⚡ Intraday", icon: "⚡" },
    { key: "short_term", label: "📅 Short Term", icon: "📅" },
    { key: "long_term", label: "🗓️ Long Term", icon: "🗓️" },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  // Reset filters when tab changes
  useEffect(() => {
    setFilterSignal("All");
    setFilterSector("All");
  }, [activeTab]);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, intraRes, shortRes, longRes] = await Promise.all([
        fetch("/api/stats", { cache: "no-store" }),
        fetch("/api/recommendations?timeframe=intraday&limit=50", { cache: "no-store" }),
        fetch("/api/recommendations?timeframe=short_term&limit=50", { cache: "no-store" }),
        fetch("/api/recommendations?timeframe=long_term&limit=50", { cache: "no-store" }),
      ]);

      const statsJson = await statsRes.json();
      const intraJson = await intraRes.json();
      const shortJson = await shortRes.json();
      const longJson = await longRes.json();

      if (statsJson.error) throw new Error(statsJson.error);

      // Group by timeframe manually
      const grouped = {
        intraday: intraJson.data || [],
        short_term: shortJson.data || [],
        long_term: longJson.data || [],
      };

      setData(grouped);
      setStats(statsJson);
    } catch (err) {
      console.error("Fetch error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const currentData = data[activeTab] || [];
  const tfStats = stats?.signalCounts?.find((s) => s.timeframe === activeTab) || {};
  const buyCount = tfStats.buy_count || 0;
  const sellCount = tfStats.sell_count || 0;
  const avgScore = tfStats.avg_score || "—";

  const latestDateRaw = stats?.stats?.latest_date;
  let latestDate = "—";
  if (latestDateRaw) {
    try {
      const d = new Date(latestDateRaw);
      if (!isNaN(d.valueOf())) {
        latestDate = d.toLocaleDateString("en-IN", {
          day: "2-digit",
          month: "short",
          year: "numeric",
        }) + " " + d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
      } else {
        latestDate = latestDateRaw.split("T")[0]; // Fallback string handling
      }
    } catch (e) {
      latestDate = "—";
    }
  }

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <div className="loading-text">Loading dashboard...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="page-header">
          <h1 className="page-title">AI Stock Advisor</h1>
          <p className="page-subtitle">ML-Powered Recommendations for Indian Markets</p>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">⚠️</div>
          <div className="empty-state-title">Connection Error</div>
          <div className="empty-state-text">
            {error}. Make sure the database is configured and the Python analysis has been run.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Header */}
      <div className="flex flex-col items-center mb-12">
        <h1 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 mb-4 tracking-tight">
          Today's Recommendations
        </h1>
        <p className="text-slate-400 mb-6">
          ML + Technical + Fundamental Analysis &middot; Updated {latestDate}
        </p>
        <RunAnalysisButton />
      </div>

      {/* Metrics */}
      <div className="metrics-grid">
        <MetricCard
          icon="🟢"
          value={buyCount}
          label="Buy Signals"
          variant="green"
        />
        <MetricCard
          icon="🔴"
          value={sellCount}
          label="Sell Signals"
          variant="red"
        />
        <MetricCard icon="📊" value={avgScore} label="Avg Score" />
        <MetricCard
          icon="📅"
          value={latestDate}
          label="Last Updated"
          variant="amber"
        />
      </div>

      {/* Timeframe Tabs */}
      <div className="tabs">
        {timeframes.map((tf) => (
          <button
            key={tf.key}
            className={`tab ${activeTab === tf.key ? "active" : ""}`}
            onClick={() => setActiveTab(tf.key)}
          >
            {tf.label}
          </button>
        ))}
      </div>

      {currentData.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <div className="empty-state-title">No {activeTab.replace("_", " ")} data</div>
          <div className="empty-state-text">
            Run the Python analysis to generate recommendations for this timeframe.
          </div>
        </div>
      ) : (
        <>
          {/* Top Picks Cards */}
          <div className="section-header">
            <h2 className="section-title">🏆 Top Picks</h2>
          </div>
          <div className="picks-grid">
            {currentData.slice(0, 6).map((stock, i) => (
              <PickCard key={stock.symbol} stock={stock} rank={i + 1} />
            ))}
          </div>

          {/* Full Table */}
          <div className="section-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
            <h2 className="section-title" style={{ margin: 0 }}>📋 Full Rankings</h2>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <input
                type="text"
                placeholder="Search symbol..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  padding: "8px 12px",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--border-color)",
                  background: "var(--bg-surface)",
                  color: "white",
                  fontSize: "0.9rem",
                  width: "160px"
                }}
              />
              <select
                value={filterSector}
                onChange={(e) => setFilterSector(e.target.value)}
                style={{
                  padding: "8px 12px",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--border-color)",
                  background: "var(--bg-surface)",
                  color: "white",
                  fontSize: "0.9rem"
                }}
              >
                <option value="All">All Sectors</option>
                {[...new Set(currentData.map((s) => s.sector).filter(Boolean))].sort().map((sec) => (
                  <option key={sec} value={sec}>{sec}</option>
                ))}
              </select>
              <select
                value={filterSignal}
                onChange={(e) => setFilterSignal(e.target.value)}
                style={{
                  padding: "8px 12px",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--border-color)",
                  background: "var(--bg-surface)",
                  color: "white",
                  fontSize: "0.9rem"
                }}
              >
                <option value="All">All Signals</option>
                <option value="Strong Buy">Strong Buy</option>
                <option value="Buy">Buy</option>
                <option value="Hold">Hold</option>
                <option value="Sell">Sell</option>
                <option value="Strong Sell">Strong Sell</option>
              </select>
            </div>
          </div>
          <div className="table-container">
            <table className="stock-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Symbol</th>
                  <th>Name</th>
                  <th>Price</th>
                  <th>Change</th>
                  <th>Score</th>
                  <th>Signal</th>
                  <th>Target 1</th>
                  <th>Target 2</th>
                  <th>Stop Loss</th>
                </tr>
              </thead>
              <tbody>
                {currentData
                  .filter((stock) => {
                    if (filterSector !== "All" && stock.sector !== filterSector) return false;
                    if (filterSignal !== "All") {
                      const sig = stock.signal ? stock.signal.toLowerCase() : "hold";
                      const fSig = filterSignal.toLowerCase();
                      if (fSig === "hold" && !sig.includes("buy") && !sig.includes("sell")) return true;
                      if (!sig.includes(fSig)) return false;
                      // Don't mix up "Buy" and "Strong Buy"
                      if (fSig === "buy" && sig.includes("strong")) return false;
                      if (fSig === "sell" && sig.includes("strong")) return false;
                    }
                    if (searchQuery.trim() !== "") {
                      const q = searchQuery.toLowerCase();
                      if (
                        !(stock.symbol && stock.symbol.toLowerCase().includes(q)) &&
                        !(stock.name && stock.name.toLowerCase().includes(q))
                      ) {
                        return false;
                      }
                    }
                    return true;
                  })
                  .map((stock, i) => {
                  const change = parseFloat(stock.change_pct || 0);
                  return (
                    <tr key={stock.symbol}>
                      <td style={{ color: "var(--text-muted)" }}>{i + 1}</td>
                      <td style={{ fontWeight: 700 }}>{stock.symbol}</td>
                      <td style={{ color: "var(--text-secondary)" }}>
                        {stock.name}
                      </td>
                      <td>₹{Number(stock.close).toLocaleString("en-IN")}</td>
                      <td
                        className={
                          change >= 0 ? "price-green" : "price-red"
                        }
                      >
                        {change >= 0 ? "+" : ""}
                        {change.toFixed(2)}%
                      </td>
                      <td>
                        <ScoreBar score={stock.composite_score || 0} />
                      </td>
                      <td>
                        <span
                          className={`signal-badge ${getSignalClass(stock.signal)}`}
                        >
                          {getSignalLabel(stock.signal)}
                        </span>
                      </td>
                      <td className="price-green">
                        ₹{Number(stock.target_1 || 0).toLocaleString("en-IN")}
                      </td>
                      <td className="price-green">
                        ₹{Number(stock.target_2 || 0).toLocaleString("en-IN")}
                      </td>
                      <td className="price-red">
                        ₹{Number(stock.stop_loss || 0).toLocaleString("en-IN")}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Score Breakdown */}
          <div style={{ marginTop: 32 }}>
            <div className="section-header">
              <h2 className="section-title">🧠 Score Breakdown (Top 10)</h2>
            </div>
            <div className="table-container">
              <table className="stock-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>ML Score</th>
                    <th>Technical</th>
                    <th>Fundamental</th>
                    <th>Composite</th>
                    <th>RSI</th>
                    <th>Vol Ratio</th>
                    <th>ATR</th>
                  </tr>
                </thead>
                <tbody>
                  {currentData.slice(0, 10).map((stock) => (
                    <tr key={`breakdown-${stock.symbol}`}>
                      <td style={{ fontWeight: 700 }}>{stock.symbol}</td>
                      <td>
                        <ScoreBar score={stock.ml_score || 0} />
                      </td>
                      <td>
                        <ScoreBar score={stock.tech_score || 0} />
                      </td>
                      <td>
                        <ScoreBar score={stock.fund_score || 0} />
                      </td>
                      <td>
                        <ScoreBar score={stock.composite_score || 0} />
                      </td>
                      <td>{Number(stock.rsi || 0).toFixed(1)}</td>
                      <td>{Number(stock.volume_ratio || 0).toFixed(2)}</td>
                      <td>₹{Number(stock.atr || 0).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Footer */}
      <footer
        style={{
          textAlign: "center",
          padding: "48px 0 24px",
          color: "var(--text-muted)",
          fontSize: "0.8rem",
        }}
      >
        <p>
          ⚠️ Not financial advice. Always do your own research before investing.
        </p>
        <p style={{ marginTop: 4 }}>
          🤖 AI Stock Advisor — Powered by ML + Technical + Fundamental Analysis
        </p>
      </footer>
    </div>
  );
}
