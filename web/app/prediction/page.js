"use client";
import { useState } from "react";

export default function PredictionPage() {
  const [symbol, setSymbol] = useState("");
  const [timeframe, setTimeframe] = useState("15 min");
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([]);

  const timeframes = ["5 min", "15 min", "1 hr", "4 hrs", "1 day", "1 week", "1 month"];

  async function handleSymbolChange(val) {
    const symbolVal = val.toUpperCase();
    setSymbol(symbolVal);
    if (symbolVal.length > 1) {
      try {
        const res = await fetch(`/api/symbols?q=${symbolVal}`);
        const data = await res.json();
        setSuggestions(data || []);
      } catch (e) {
        console.error("Failed to fetch suggestions:", e);
      }
    } else {
      setSuggestions([]);
    }
  }

  async function handlePredict() {
    if (!symbol) {
      setError("Please enter a stock symbol");
      return;
    }
    setLoading(true);
    setError(null);
    setPrediction(null);

    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol, timeframe }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setPrediction(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function getSentimentColor(sentiment) {
    const s = sentiment?.toLowerCase() || "";
    if (s.includes("bullish")) return "#10b981";
    if (s.includes("bearish")) return "#ef4444";
    if (s.includes("neutral")) return "#64748b";
    return "var(--text-muted)";
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">AI Stock Predictor</h1>
        <p className="page-subtitle">
          Advanced directional movement prediction powered by Gemini 2.5 Flash AI
        </p>
      </div>

      <div className="table-container" style={{ padding: 24, marginBottom: 32 }}>
        <div style={{ display: "flex", gap: 16, alignItems: "flex-end", flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: "200px" }}>
            <label className="metric-label" style={{ display: "block", marginBottom: 8 }}>Stock Symbol</label>
            <input
              type="text"
              placeholder="e.g. RELIANCE, TCS, INFY"
              value={symbol}
              onChange={(e) => handleSymbolChange(e.target.value)}
              list="stock-suggestions"
              style={{
                width: "100%",
                padding: "12px",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-color)",
                background: "var(--bg-surface)",
                color: "white"
              }}
            />
            <datalist id="stock-suggestions">
              {suggestions.map((s) => (
                <option key={s.symbol} value={s.symbol}>{s.name}</option>
              ))}
            </datalist>
          </div>
          <div style={{ flex: 1, minWidth: "200px" }}>
            <label className="metric-label" style={{ display: "block", marginBottom: 8 }}>Timeframe</label>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              style={{
                width: "100%",
                padding: "12px",
                borderRadius: "var(--radius-md)",
                border: "1px solid var(--border-color)",
                background: "var(--bg-surface)",
                color: "white"
              }}
            >
              {timeframes.map((tf) => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
          </div>
          <button
            onClick={handlePredict}
            disabled={loading}
            className="btn-primary"
            style={{
              padding: "12px 24px",
              height: "48px",
              background: "var(--gradient-primary)",
              color: "white",
              border: "none",
              borderRadius: "var(--radius-md)",
              cursor: loading ? "not-allowed" : "pointer",
              fontWeight: 600
            }}
          >
            {loading ? "🔮 Predicting..." : "Generate Prediction"}
          </button>
        </div>
      </div>

      {error && (
        <div className="empty-state" style={{ marginBottom: 32, borderColor: "#ef4444" }}>
          <div className="empty-state-icon">⚠️</div>
          <div className="empty-state-text" style={{ color: "#ef4444" }}>{error}</div>
        </div>
      )}

      {prediction && (
        <div className="prediction-results" style={{ animation: "fadeIn 0.5s ease" }}>
          {/* Top Summary Header */}
          <div className="table-container" style={{ padding: 24, marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center", borderLeft: `6px solid ${getSentimentColor(prediction.sentiment)}` }}>
            <div>
              <div style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginBottom: 4 }}>CURRENT SENTIMENT</div>
              <div style={{ fontSize: "1.8rem", fontWeight: 800, color: getSentimentColor(prediction.sentiment) }}>
                {prediction.sentiment?.toUpperCase()}
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginBottom: 4 }}>CURRENT PRICE</div>
              <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "white" }}>
                ₹{Number(prediction.currentPrice).toLocaleString("en-IN")}
              </div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 24, marginBottom: 24 }}>
            {/* S/R Levels */}
            <div className="table-container" style={{ padding: 24 }}>
              <h2 className="section-title" style={{ fontSize: "1.1rem", marginBottom: 20 }}>🎯 Technical Levels</h2>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginBottom: 8 }}>RESISTANCE</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    <div style={{ background: "rgba(239, 68, 68, 0.1)", color: "#ef4444", padding: "8px 12px", borderRadius: 4, display: "flex", justifyContent: "space-between" }}>
                      <span>R3</span> <b>₹{prediction.levels?.r3}</b>
                    </div>
                    <div style={{ background: "rgba(239, 68, 68, 0.1)", color: "#ef4444", padding: "8px 12px", borderRadius: 4, display: "flex", justifyContent: "space-between" }}>
                      <span>R2</span> <b>₹{prediction.levels?.r2}</b>
                    </div>
                    <div style={{ background: "rgba(239, 68, 68, 0.1)", color: "#ef4444", padding: "8px 12px", borderRadius: 4, display: "flex", justifyContent: "space-between" }}>
                      <span>R1</span> <b>₹{prediction.levels?.r1}</b>
                    </div>
                  </div>
                </div>
                <div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginBottom: 8 }}>SUPPORT</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    <div style={{ background: "rgba(16, 185, 129, 0.1)", color: "#10b981", padding: "8px 12px", borderRadius: 4, display: "flex", justifyContent: "space-between" }}>
                      <span>S1</span> <b>₹{prediction.levels?.s1}</b>
                    </div>
                    <div style={{ background: "rgba(16, 185, 129, 0.1)", color: "#10b981", padding: "8px 12px", borderRadius: 4, display: "flex", justifyContent: "space-between" }}>
                      <span>S2</span> <b>₹{prediction.levels?.s2}</b>
                    </div>
                    <div style={{ background: "rgba(16, 185, 129, 0.1)", color: "#10b981", padding: "8px 12px", borderRadius: 4, display: "flex", justifyContent: "space-between" }}>
                      <span>S3</span> <b>₹{prediction.levels?.s3}</b>
                    </div>
                  </div>
                </div>
              </div>
              <div style={{ marginTop: 20, textAlign: "center", borderTop: "1px solid var(--border-color)", paddingTop: 16 }}>
                <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>PIVOT POINT: </span>
                <span style={{ fontWeight: 700, fontSize: "1.1rem", color: "#3b82f6" }}>₹{prediction.levels?.pivot}</span>
              </div>
            </div>

            {/* Indicators Card */}
            <div className="table-container" style={{ padding: 24 }}>
              <h2 className="section-title" style={{ fontSize: "1.1rem", marginBottom: 20 }}>📉 Indicators</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ color: "var(--text-secondary)" }}>RSI (14)</span>
                  <span style={{ 
                    padding: "4px 12px", 
                    borderRadius: 20, 
                    background: prediction.levels?.rsi > 70 ? "rgba(239, 68, 68, 0.2)" : (prediction.levels?.rsi < 30 ? "rgba(16, 185, 129, 0.2)" : "rgba(59, 130, 246, 0.2)"),
                    color: prediction.levels?.rsi > 70 ? "#ef4444" : (prediction.levels?.rsi < 30 ? "#10b981" : "#3b82f6"),
                    fontWeight: 700
                  }}>
                    {prediction.levels?.rsi || "N/A"}
                  </span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ color: "var(--text-secondary)" }}>MACD Signal</span>
                  <span style={{ 
                    color: prediction.levels?.macd > 0 ? "#10b981" : "#ef4444",
                    fontWeight: 700
                  }}>
                    {prediction.levels?.macd > 0 ? "+" : ""}{prediction.levels?.macd || "N/A"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="table-container" style={{ padding: 32 }}>
            <h2 className="section-title">📊 Detail Analysis</h2>
            <div style={{ lineHeight: 1.6, color: "var(--text-secondary)", whiteSpace: "pre-wrap" }}>
              {prediction.technicalAnalysis}
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>AI is analyzing the market structure for {symbol} ({timeframe})...</p>
        </div>
      )}
    </div>
  );
}
