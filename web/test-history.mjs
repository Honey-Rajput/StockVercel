import { neon } from "@neondatabase/serverless";
import dotenv from "dotenv";

dotenv.config({ path: ".env.local" }); // Or whatever Next uses
if (!process.env.DATABASE_URL) {
  dotenv.config({ path: "../.env" });
}

const sql = neon(process.env.DATABASE_URL);

async function test() {
  try {
    const dates = await sql`
      SELECT DISTINCT date FROM recommendations
      ORDER BY date DESC LIMIT 5
    `;
    console.log("DATES:", dates);
    
    if (dates.length === 0) {
      console.log("No dates found");
      return;
    }
    const dateList = dates.map((d) => d.date);
    console.log("DATELIST:", dateList);
    
    const rows = await sql`
      SELECT * FROM recommendations
      WHERE date = ANY(${dateList})
      AND timeframe = 'long_term'
      ORDER BY date DESC, rank ASC
    `;
    console.log("ROWS:", rows.length);
  } catch(e) {
    console.error("ERROR:", e);
  }
}

test();
