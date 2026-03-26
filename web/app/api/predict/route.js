import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { getDb } from "@/lib/db";

// Function to manually load .env from parent directory if not in process.env
function getApiKey() {
  if (process.env.EURI_API_KEY) return process.env.EURI_API_KEY;
  
  try {
    const envPath = path.resolve(process.cwd(), "..", ".env");
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, "utf-8");
      const match = envContent.match(/^EURI_API_KEY=(.*)$/m);
      if (match) return match[1].trim();
    }
  } catch (e) {
    console.error("Error reading .env:", e);
  }
  return null;
}

export async function POST(request) {
  try {
    const { symbol, timeframe } = await request.json();
    const apiKey = getApiKey();
    const sql = getDb();

    if (!apiKey) {
      return NextResponse.json({ error: "EURI_API_KEY not found in configuration" }, { status: 500 });
    }

    // 1. Fetch latest stats from DB for this symbol
    const dbStats = await sql`
      SELECT close, rsi, macd_hist, target_1, target_2, stop_loss, timeframe as db_tf
      FROM recommendations
      WHERE symbol = ${symbol.toUpperCase()}
      ORDER BY date DESC
      LIMIT 1
    `;

    const stats = dbStats[0] || {};
    const statsContext = stats.close ? `
      Latest Database Snapshot for ${symbol}:
      - Current Price: ₹${stats.close}
      - RSI: ${stats.rsi || "N/A"}
      - MACD Histogram: ${stats.macd_hist || "N/A"}
      - System Targets: ₹${stats.target_1}, ₹${stats.target_2}
      - System Stop Loss: ₹${stats.stop_loss}
    ` : "No recent database metrics found for this symbol.";

    const prompt = `You are a Senior Technical Trading Analyst. Analyze "${symbol}" for the "${timeframe}" timeframe.
    
    ${statsContext}

    IMPORTANT: You must respond ONLY with a valid JSON object. 
    Format:
    {
      "sentiment": "Bullish" | "Bearish" | "Neutral" | "Ignore",
      "currentPrice": number,
      "technicalAnalysis": "detailed text analysis...",
      "levels": {
        "pivot": number,
        "s1": number, "s2": number, "s3": number,
        "r1": number, "r2": number, "r3": number,
        "rsi": number | null,
        "macd": number | null
      }
    }

    Notes: 
    - Calculate Pivot Points, S1-S3, and R1-R3 based on the current price and market structure for the given timeframe.
    - Provide deep technical justification in technicalAnalysis.
    - Ensure currentPrice matches the latest provided price if available.`;

    const response = await fetch("https://api.euron.one/api/v1/euri/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "gemini-2.5-flash",
        messages: [
          { role: "system", content: "You are an expert financial analyst. You only speak JSON." },
          { role: "user", content: prompt }
        ],
        temperature: 0.7,
        response_format: { type: "json_object" }
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    let result;
    try {
      const content = data.choices?.[0]?.message?.content || "{}";
      // Handle potential markdown code blocks in response
      const jsonStr = content.replace(/```json/g, "").replace(/```/g, "").trim();
      result = JSON.parse(jsonStr);
    } catch (e) {
      console.error("Failed to parse AI JSON:", data.choices?.[0]?.message?.content);
      throw new Error("AI returned invalid data format. Please try again.");
    }

    return NextResponse.json(result);
  } catch (error) {
    console.error("Prediction API Error:", error);
    return NextResponse.json({ error: error.message || "Failed to generate prediction" }, { status: 500 });
  }
}

