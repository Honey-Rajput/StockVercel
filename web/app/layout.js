import "./globals.css";

export const metadata = {
  title: "AI Stock Advisor — ML-Powered Recommendations",
  description:
    "Automated ML stock recommendation system for Indian markets. Get intraday, short-term, and long-term picks powered by Random Forest + XGBoost ensemble analysis.",
  keywords:
    "stock recommendations, AI trading, NSE stocks, machine learning, technical analysis, Indian stock market",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <nav className="navbar">
          <a href="/" className="navbar-brand">
            📈 <span>AI Stock Advisor</span>
          </a>

          <ul className="navbar-links">
            <li>
              <a href="/" className="active">📊 Dashboard</a>
            </li>
            <li>
              <a href="/history">📜 History</a>
            </li>
            <li>
              <a href="/prediction">🔮 Prediction</a>
            </li>
          </ul>

          <div className="navbar-status">
            <span className="status-dot"></span>
            <span>Live</span>
          </div>
        </nav>

        {children}
      </body>
    </html>
  );
}
