import { getDb } from "@/lib/db";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get("q") || "";
    const sql = getDb();

    // Fetch unique symbols matching the query
    const symbols = await sql`
      SELECT DISTINCT symbol, name
      FROM recommendations
      WHERE symbol ILIKE ${query + "%"}
      OR name ILIKE ${"%" + query + "%"}
      LIMIT 10
    `;

    return NextResponse.json(symbols);
  } catch (error) {
    console.error("Symbols API Error:", error);
    return NextResponse.json({ error: "Failed to fetch symbols" }, { status: 500 });
  }
}
