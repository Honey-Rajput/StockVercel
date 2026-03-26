import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";

const execAsync = promisify(exec);

export async function POST() {
  try {
    // Determine the path to the python script
    const scriptPath = path.join(process.cwd(), "..", "run_analysis.py");
    console.log("Triggering Python script:", scriptPath);
    
    // Write python output to log file to debug crashes
    exec(`python "${scriptPath}" > analysis_log.txt 2>&1`, { 
      cwd: path.join(process.cwd(), ".."),
      env: { ...process.env, PYTHONIOENCODING: "utf-8" }
    }, (error, stdout, stderr) => {
      if (error) {
        console.error(`exec error: ${error}`);
        return;
      }
    });

    return NextResponse.json({ 
      success: true, 
      message: "Analysis started! This will take a few minutes for 2000+ stocks. Check the node terminal for logs." 
    });
  } catch (error) {
    console.error("Run error:", error);
    return NextResponse.json(
      { error: error.message || "Failed to run analysis" },
      { status: 500 }
    );
  }
}
