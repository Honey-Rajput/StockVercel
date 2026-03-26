import { getDb } from "@/lib/db";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST() {
  try {
    const sql = getDb();

    await sql`
      CREATE TABLE IF NOT EXISTS recommendations (
        id SERIAL PRIMARY KEY,
        date DATE NOT NULL,
        timeframe VARCHAR(20) NOT NULL,
        rank INT,
        symbol VARCHAR(20) NOT NULL,
        name VARCHAR(100),
        sector VARCHAR(50),
        close DECIMAL(12,2),
        change_pct DECIMAL(8,2),
        ml_score DECIMAL(6,2),
        tech_score DECIMAL(6,2),
        fund_score DECIMAL(6,2),
        composite_score DECIMAL(6,2),
        signal VARCHAR(30),
        entry_price DECIMAL(12,2),
        stop_loss DECIMAL(12,2),
        target_1 DECIMAL(12,2),
        target_2 DECIMAL(12,2),
        rsi DECIMAL(6,2),
        macd_hist DECIMAL(12,4),
        volume_ratio DECIMAL(8,2),
        atr DECIMAL(12,2),
        pe DECIMAL(8,2),
        roe DECIMAL(8,4),
        created_at TIMESTAMP DEFAULT NOW()
      )
    `;

    await sql`CREATE INDEX IF NOT EXISTS idx_rec_date ON recommendations(date)`;
    await sql`CREATE INDEX IF NOT EXISTS idx_rec_timeframe ON recommendations(timeframe)`;
    await sql`CREATE INDEX IF NOT EXISTS idx_rec_symbol ON recommendations(symbol)`;

    await sql`
      CREATE TABLE IF NOT EXISTS backtest_results (
        id SERIAL PRIMARY KEY,
        symbol VARCHAR(20) NOT NULL,
        timeframe VARCHAR(20),
        initial_capital DECIMAL(14,2),
        final_value DECIMAL(14,2),
        total_return_pct DECIMAL(8,2),
        buy_hold_return_pct DECIMAL(8,2),
        alpha DECIMAL(8,2),
        total_trades INT,
        win_rate_pct DECIMAL(6,2),
        sharpe_ratio DECIMAL(6,2),
        max_drawdown_pct DECIMAL(8,2),
        profit_factor DECIMAL(8,2),
        created_at TIMESTAMP DEFAULT NOW()
      )
    `;

    await sql`
      CREATE TABLE IF NOT EXISTS stock_universe (
        symbol VARCHAR(20) PRIMARY KEY,
        name VARCHAR(100),
        sector VARCHAR(50),
        market_cap_category VARCHAR(30)
      )
    `;

    return NextResponse.json({ success: true, message: "Database initialized successfully" });
  } catch (error) {
    console.error("Init DB Error:", error);
    return NextResponse.json(
      { error: error.message || "Failed to initialize database" },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({
    message: "Send a POST request to this endpoint to initialize the database tables.",
  });
}
