import { getDb } from "@/lib/db";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request) {
  try {
    const data = await request.json();
    const sql = getDb();
    
    // Support bulk inserts
    if (Array.isArray(data.recommendations)) {
      const recs = data.recommendations;
      console.log(`Saving ${recs.length} recommendations via API...`);
      
      for (const row of recs) {
        await sql`
          INSERT INTO recommendations (
              date, timeframe, rank, symbol, name, sector, 
              close, change_pct, ml_score, tech_score, fund_score, 
              composite_score, signal, entry_price, stop_loss, target_1, target_2,
              rsi, macd_hist, volume_ratio, atr, pe, roe
          ) VALUES (
              ${row.date}, ${row.timeframe}, ${row.rank}, ${row.symbol}, ${row.name}, ${row.sector},
              ${row.close}, ${row.change_pct}, ${row.ml_score}, ${row.tech_score}, ${row.fund_score},
              ${row.composite_score}, ${row.signal}, ${row.entry_price}, ${row.stop_loss}, ${row.target_1}, ${row.target_2},
              ${row.rsi}, ${row.macd_hist}, ${row.volume_ratio}, ${row.atr}, ${row.pe}, ${row.roe}
          )
        `;
      }
      return NextResponse.json({ success: true, inserted: recs.length });
    }
    
    return NextResponse.json({ error: "Invalid format. Expected 'recommendations' array." }, { status: 400 });

  } catch (error) {
    console.error("Save API Error:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
