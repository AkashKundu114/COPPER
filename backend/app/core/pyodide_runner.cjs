/**
 * Pyodide WebAssembly Sandbox Runner
 * Executes untrusted Python code inside an isolated WebAssembly VM.
 */
const fs = require("fs");
const path = require("path");

// Ensure pyodide can be resolved from backend node_modules
let pyodideModule;
try {
    pyodideModule = require("pyodide");
} catch (e) {
    // Fallback: direct relative resolution
    const candidatePath = path.resolve(__dirname, "../../node_modules/pyodide");
    pyodideModule = require(candidatePath);
}

const { loadPyodide } = pyodideModule;

async function run() {
    let stdout = "";
    let stderr = "";

    try {
        const rawInput = fs.readFileSync(0, "utf-8");
        const payload = rawInput.trim() ? JSON.parse(rawInput) : {};
        const code = payload.code || "";
        const allowNetwork = Boolean(payload.allow_network);

        // Network isolation: strip network access primitives unless explicitly allowed
        if (!allowNetwork) {
            if (typeof globalThis.fetch !== "undefined") {
                globalThis.fetch = () => {
                    throw new Error("NetworkAccessBlocked: Network disabled in sandbox");
                };
            }
            if (typeof globalThis.WebSocket !== "undefined") {
                globalThis.WebSocket = undefined;
            }
            if (typeof globalThis.XMLHttpRequest !== "undefined") {
                globalThis.XMLHttpRequest = undefined;
            }
        }

        const pyodide = await loadPyodide({
            stdout: (text) => {
                stdout += text + "\n";
            },
            stderr: (text) => {
                stderr += text + "\n";
            }
        });

        const result = pyodide.runPython(code);
        if (result !== undefined && result !== null && typeof result.destroy === "function") {
            result.destroy();
        }

        const output = {
            stdout: stdout,
            stderr: stderr,
            exit_code: 0,
            error: null
        };
        process.stdout.write(JSON.stringify(output));
    } catch (err) {
        let errMessage = err && err.message ? String(err.message) : String(err);
        let errorType = err && err.name ? String(err.name) : "ExecutionError";

        if (errMessage.includes("Error:") || errMessage.includes("Traceback")) {
            errorType = "PythonError";
        }

        const output = {
            stdout: stdout,
            stderr: stderr ? `${stderr}\n${errMessage}` : errMessage,
            exit_code: 1,
            error: errorType
        };
        process.stdout.write(JSON.stringify(output));
    }
}

run();
