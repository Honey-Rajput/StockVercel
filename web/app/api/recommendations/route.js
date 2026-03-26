import { getDb } from "@/lib/db";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request) {
  try {
    const sql = getDb();
    const { searchParams } = new URL(request.url);
    const timeframe = searchParams.get("timeframe");
    const limit = parseInt(searchParams.get("limit") || "50");

    let rows;
    if (timeframe) {
      rows = await sql`
        SELECT * FROM recommendations
        WHERE date = (SELECT MAX(date) FROM recommendations)
        AND timeframe = ${timeframe}
        ORDER BY rank ASC
        LIMIT ${limit}
      `;
    } else {
      rows = await sql`
        SELECT * FROM recommendations
        WHERE date = (SELECT MAX(date) FROM recommendations)
        ORDER BY timeframe, rank ASC
        LIMIT ${limit * 3}
      `;
    }

    return NextResponse.json({ data: rows, count: rows.length });
  } catch (error) {
    console.error("API Error:", error);
    return NextResponse.json(
      { error: error.message || "Failed to fetch recommendations" },
      { status: 500 }
    );
  }
}
