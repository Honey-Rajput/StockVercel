"use client";
import { useState, useEffect } from "react";

function getScoreColor(score) {
  if (score >= 80) return "#10b981";
  if (score >= 65) return "#3b82f6";
  if (score >= 50) return "#f59e0b";
  if (score >= 35) return "#f97316";
  return "#ef4444";
}

function getScoreBg(score) {
  if (score >= 80) return "rgba(16, 185, 129, 0.2)";
  if (score >= 65) return "rgba(59, 130, 246, 0.2)";
  if (score >= 50) return "rgba(245, 158, 11, 0.2)";
  if (score >= 35) return "rgba(249, 115, 22, 0.2)";
  return "rgba(239, 68, 68, 0.2)";
}

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

export default function HistoryPage() {
  const [data, setData] = useState([]);
  const [dates, setDates] = useState([]);
  const [timeframe, setTimeframe] = useState("long_term");
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  const timeframes = [
    { key: "intraday", label: "⚡ Intraday" },
    { key: "short_term", label: "📅 Short Term" },
    { key: "long_term", label: "🗓️ Long Term" },
  ];

  useEffect(() => {
    fetchHistory();
  }, [timeframe]);

  async function fetchHistory() {
    setLoading(true);
    try {
      const res = await fetch(`/api/history?timeframe=${timeframe}&days=5`, { cache: "no-store" });
      const json = await res.json();
      setData(json.data || []);
      setDates(json.dates || []);
      if (json.dates && json.dates.length > 0) {
        setSelectedDate(json.dates[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  // Group data by symbol for heatmap
  const symbolMap = {};
  for (const row of data) {
    const dateStr =
      typeof row.date === "string"
        ? row.date.split("T")[0]
        : new Date(row.date).toISOString().split("T")[0];
    if (!symbolMap[row.symbol]) symbolMap[row.symbol] = {};
    symbolMap[row.symbol][dateStr] = row;
  }
  
  let symbols = Object.keys(symbolMap).sort();
  if (searchQuery.trim() !== "") {
    const q = searchQuery.toLowerCase();
    symbols = symbols.filter(sym => sym.toLowerCase().includes(q));
  }

  // Data for selected date
  const dateData = data.filter((r) => {
    const d =
      typeof r.date === "string"
        ? r.date.split("T")[0]
        : new Date(r.date).toISOString().split("T")[0];
    return d === selectedDate;
  });

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <div className="loading-text">Loading history...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Week History</h1>
        <p className="page-subtitle">
          Past 5 trading days at a glance — track how picks perform over time
        </p>
      </div>

      {/* Timeframe Tabs */}
      <div className="tabs">
        {timeframes.map((tf) => (
          <button
            key={tf.key}
            className={`tab ${timeframe === tf.key ? "active" : ""}`}
            onClick={() => setTimeframe(tf.key)}
          >
            {tf.label}
          </button>
        ))}
      </div>

      {dates.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📜</div>
          <div className="empty-state-title">No history yet</div>
          <div className="empty-state-text">
            Run the Python analysis on consecutive days to build up history data.
          </div>
        </div>
      ) : (
        <>
          {/* Score Heatmap */}
          <div className="section-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
            <h2 className="section-title" style={{ margin: 0 }}>🗺️ Score Heatmap</h2>
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
          </div>
          <div className="table-container" style={{ marginBottom: 32 }}>
            <div style={{ overflowX: "auto" }}>
              <table className="stock-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    {dates.map((d) => (
                      <th key={d} style={{ textAlign: "center" }}>
                        {new Date(d + "T00:00:00").toLocaleDateString("en-IN", {
                          day: "2-digit",
                          month: "short",
                        })}
                      </th>
                    ))}
                    <th style={{ textAlign: "center" }}>Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {symbols.slice(0, 20).map((sym) => {
                    const scores = dates.map(
                      (d) => symbolMap[sym]?.[d]?.composite_score || null
                    );
                    const validScores = scores.filter((s) => s !== null);
                    const trend =
                      validScores.length >= 2
                        ? validScores[0] - validScores[validScores.length - 1]
                        : 0;

                    return (
                      <tr key={sym}>
                        <td style={{ fontWeight: 700 }}>{sym}</td>
                        {dates.map((d) => {
                          const score =
                            symbolMap[sym]?.[d]?.composite_score || null;
                          return (
                            <td key={d} style={{ textAlign: "center" }}>
                              {score !== null ? (
                                <span
                                  className="heatmap-cell"
                                  style={{
                                    display: "inline-flex",
                                    background: getScoreBg(score),
                                    color: getScoreColor(score),
                                    minWidth: 48,
                                  }}
                                >
                                  {Math.round(score)}
                                </span>
                              ) : (
                                <span style={{ color: "var(--text-muted)" }}>
                                  —
                                </span>
                              )}
                            </td>
                          );
                        })}
                        <td style={{ textAlign: "center" }}>
                          <span
                            style={{
                              color:
                                trend > 0
                                  ? "#10b981"
                                  : trend < 0
                                  ? "#ef4444"
                                  : "var(--text-muted)",
                              fontWeight: 600,
                            }}
                          >
                            {trend > 0 ? "▲" : trend < 0 ? "▼" : "—"}{" "}
                            {Math.abs(trend).toFixed(1)}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Date Selector */}
          <div className="section-header">
            <h2 className="section-title">📋 Day Details</h2>
            <div className="tabs" style={{ marginBottom: 0 }}>
              {dates.map((d) => (
                <button
                  key={d}
                  className={`tab ${selectedDate === d ? "active" : ""}`}
                  onClick={() => setSelectedDate(d)}
                >
                  {new Date(d + "T00:00:00").toLocaleDateString("en-IN", {
                    day: "2-digit",
                    month: "short",
                  })}
                </button>
              ))}
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
                  <th>Score</th>
                  <th>Signal</th>
                  <th>Target</th>
                  <th>Stop Loss</th>
                </tr>
              </thead>
              <tbody>
                {dateData.filter(stock => {
                  if (searchQuery.trim() === "") return true;
                  return (stock.symbol && stock.symbol.toLowerCase().includes(searchQuery.toLowerCase())) ||
                         (stock.name && stock.name.toLowerCase().includes(searchQuery.toLowerCase()));
                }).map((stock, i) => (
                  <tr key={stock.symbol}>
                    <td style={{ color: "var(--text-muted)" }}>{i + 1}</td>
                    <td style={{ fontWeight: 700 }}>{stock.symbol}</td>
                    <td style={{ color: "var(--text-secondary)" }}>
                      {stock.name}
                    </td>
                    <td>
                      ₹{Number(stock.close).toLocaleString("en-IN")}
                    </td>
                    <td>
                      <span
                        className="heatmap-cell"
                        style={{
                          display: "inline-flex",
                          background: getScoreBg(stock.composite_score),
                          color: getScoreColor(stock.composite_score),
                        }}
                      >
                        {Math.round(stock.composite_score || 0)}
                      </span>
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
                    <td className="price-red">
                      ₹{Number(stock.stop_loss || 0).toLocaleString("en-IN")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
