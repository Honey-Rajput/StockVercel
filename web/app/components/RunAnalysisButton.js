"use client";

import { useState, useEffect } from "react";

export default function RunAnalysisButton() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [progress, setProgress] = useState(null);

  useEffect(() => {
    let interval;
    if (loading) {
      interval = setInterval(async () => {
        try {
          const res = await fetch("/api/progress");
          const data = await res.json();
          
          if (data.status === "idle") {
            if (progress && progress.current > 0) {
              setLoading(false);
              setProgress(null);
              setMessage("Analysis Complete! Refreshing...");
              setTimeout(() => window.location.reload(), 2000);
            }
          } else {
            setProgress(data);
            setMessage(data.status);
          }
        } catch (e) {
          console.error(e);
        }
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [loading, progress]);

  const handleRun = async () => {
    setLoading(true);
    setProgress({ current: 0, total: 100, phase: "Initializing AI Engine..." });
    setMessage("Connecting to Python ML pipeline...");
    
    try {
      await fetch("/api/run-analysis", { method: "POST" });
    } catch (err) {
      setMessage("Failed to ignite ML Engine.");
      setLoading(false);
    }
  };

  const percentage = progress && progress.total > 0 
    ? Math.round((progress.current / progress.total) * 100) 
    : 0;

  return (
    <div className="ai-btn-container">
      {!loading ? (
        <button onClick={handleRun} className="ai-run-btn">
          <span className="ai-btn-bg"></span>
          <span className="ai-btn-shine"></span>
          <span className="ai-btn-content">
            <svg className="ai-btn-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Ignite ML Pipeline
          </span>
        </button>
      ) : (
        <div className="ai-progress-card">
          <div className="ai-progress-rim"></div>
          
          <div className="ai-progress-header">
            <span className="ai-progress-phase">
              {progress?.phase || "Running"}
            </span>
            <span className="ai-progress-pct">
              {percentage}%
            </span>
          </div>
          
          <div className="ai-progress-track">
            <div className="ai-progress-fill" style={{ width: `${percentage}%` }}>
              <div className="ai-progress-glow"></div>
            </div>
          </div>
          
          <p className="ai-progress-log" title={message}>
            <span className="ai-log-arrow">❯</span>
            {message}
            <span className="ai-log-cursor">_</span>
          </p>
        </div>
      )}
    </div>
  );
}
