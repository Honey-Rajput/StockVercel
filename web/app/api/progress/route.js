import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const progressFile = path.join(process.cwd(), "..", "progress.json");
    
    if (!fs.existsSync(progressFile)) {
      return NextResponse.json({ status: "idle" });
    }
    
    const content = fs.readFileSync(progressFile, "utf-8");
    const data = JSON.parse(content);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ status: "idle", error: error.message });
  }
}
