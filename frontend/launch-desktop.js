import { spawn } from "node:child_process";
import fs from "node:fs";

const chromePath = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const edgePath = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";

function launch() {
  const url = "http://localhost:5173";
  const args = [`--app=${url}`, "--window-size=1360,860"];

  let bin = null;
  if (fs.existsSync(chromePath)) {
    bin = chromePath;
  } else if (fs.existsSync(edgePath)) {
    bin = edgePath;
  }

  if (bin) {
    console.log(`[*] Launching C.O.P.P.E.R. in Standalone App Window (${bin})...`);
    const child = spawn(bin, args, { detached: true, stdio: "ignore" });
    child.unref();
  } else {
    console.log("[*] Opening C.O.P.P.E.R. in default browser...");
    const child = spawn("cmd.exe", ["/c", "start", url], { detached: true, stdio: "ignore" });
    child.unref();
  }
}

launch();
