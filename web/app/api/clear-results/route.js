import { getDb } from "@/lib/db";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request) {
  try {
    const data = await request.json();
    const date = data.date;
    
    if (!date) {
      return NextResponse.json({ error: "Date parameter required" }, { status: 400 });
    }
    
    const sql = getDb();
    
    // Clear today's recommendations so we don't get duplicates when the engine re-runs
    await sql`DELETE FROM recommendations WHERE date = ${date}`;
    
    return NextResponse.json({ success: true, message: `Cleared recommendations for ${date}` });

  } catch (error) {
    console.error("Clear API Error:", error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
