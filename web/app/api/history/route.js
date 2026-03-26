import { getDb } from "@/lib/db";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(request) {
  try {
    const sql = getDb();
    const { searchParams } = new URL(request.url);
    const days = parseInt(searchParams.get("days") || "5");
    const timeframe = searchParams.get("timeframe") || "long_term";

    const rows = await sql`
      SELECT * FROM recommendations
      WHERE timeframe = ${timeframe}
      AND date IN (
        SELECT date FROM (
          SELECT DISTINCT date FROM recommendations
          ORDER BY date DESC LIMIT ${days}
        ) as td
      )
      ORDER BY date DESC, rank ASC
    `;

    if (rows.length === 0) {
      return NextResponse.json({ data: [], dates: [] });
    }

    const uniqueDates = [...new Set(rows.map(r => {
      return typeof r.date === "string"
        ? r.date.split("T")[0]
        : new Date(r.date).toISOString().split("T")[0];
    }))];

    return NextResponse.json({
      data: rows,
      dates: uniqueDates,
    });
  } catch (error) {
    console.error("History API Error:", error);
    return NextResponse.json(
      { error: error.message || "Failed to fetch history" },
      { status: 500 }
    );
  }
}
