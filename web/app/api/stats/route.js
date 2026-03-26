import { getDb } from "@/lib/db";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const sql = getDb();

    const stats = await sql`
      SELECT
        MAX(date) as latest_date,
        COUNT(DISTINCT symbol) as total_stocks,
        COUNT(DISTINCT date) as total_days
      FROM recommendations
      WHERE date = (SELECT MAX(date) FROM recommendations)
    `;

    const signalCounts = await sql`
      SELECT
        timeframe,
        COUNT(CASE WHEN signal LIKE '%Strong Buy%' THEN 1 END) as buy_count,
        COUNT(CASE WHEN signal LIKE '%Strong Sell%' THEN 1 END) as sell_count,
        COUNT(CASE WHEN signal LIKE '%Hold%' THEN 1 END) as hold_count,
        ROUND(AVG(composite_score)::numeric, 1) as avg_score,
        MAX(composite_score) as top_score
      FROM recommendations
      WHERE date = (SELECT MAX(date) FROM recommendations)
      GROUP BY timeframe
    `;

    const topPicks = await sql`
      SELECT symbol, name, composite_score, signal, timeframe, close
      FROM recommendations
      WHERE date = (SELECT MAX(date) FROM recommendations)
      AND rank <= 3
      ORDER BY timeframe, rank
    `;

    return NextResponse.json({
      stats: stats[0] || {},
      signalCounts,
      topPicks,
    });
  } catch (error) {
    console.error("Stats API Error:", error);
    return NextResponse.json(
      { error: error.message || "Failed to fetch stats" },
      { status: 500 }
    );
  }
}
