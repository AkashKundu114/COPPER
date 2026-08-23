# ──────────────────────────────────────────────────────────────────────────────
# C.O.P.P.E.R. Local AI Models Directory Organizer
# ──────────────────────────────────────────────────────────────────────────────

$ROOT_DIR = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$base = Join-Path $ROOT_DIR "ai-models"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "         C.O.P.P.E.R. MODEL DIRECTORY STRUCTURING                " -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan

$dirs = @(
    "$base\core",
    "$base\vision",
    "$base\embeddings",
    "$base\audio\tts",
    "$base\audio\whisper",
    "$base\subagents\firewall",
    "$base\subagents\router",
    "$base\subagents\memory",
    "$base\subagents\summarizer",
    "$base\subagents\guardian",
    "$base\subagents\coding",
    "$base\subagents\shell",
    "$base\subagents\diagnostics",
    "$base\subagents\schema",
    "$base\subagents\sql",
    "$base\subagents\git",
    "$base\subagents\planner",
    "$base\subagents\search"
)

foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Force -Path $d | Out-Null
    }
}

# Cleanup top-level empty tts / whisper directories if necessary
if (Test-Path "$base\tts") { Remove-Item "$base\tts" -Force -Recurse }
if (Test-Path "$base\whisper") { Remove-Item "$base\whisper" -Force -Recurse }

# Move models to appropriate folders
$moves = @{
    "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf" = "$base\core"
    "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf" = "$base\core"
    "Mistral-7B-Instruct-v0.3-Q4_K_M.gguf" = "$base\core"
    "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf" = "$base\core"

    "Qwen2-VL-7B-Instruct-Q4_K_M.gguf" = "$base\vision"
    "Qwen2-VL-2B-Instruct-Q4_K_M.gguf" = "$base\vision"

    "nomic-embed-text-v1.5.Q4_K_M.gguf" = "$base\embeddings"

    "Qwen2.5-0.5B-Instruct-Q4_K_M.gguf" = "$base\subagents\firewall"
    "Llama-3.2-1B-Instruct-Q4_K_M.gguf" = "$base\subagents\router"
    "SmolLM2-1.7B-Instruct-Q4_K_M.gguf" = "$base\subagents\memory"
    "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf" = "$base\subagents\summarizer"
    "Llama-3.2-3B-Instruct-Q4_K_M.gguf" = "$base\subagents\guardian"
    "Qwen2.5-Coder-0.5B-Instruct-Q4_K_M.gguf" = "$base\subagents\coding"
    "Qwen2.5-Coder-1.5B-Instruct-Q4_K_M.gguf" = "$base\subagents\coding"
    "Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf" = "$base\subagents\shell"
    "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf" = "$base\subagents\diagnostics"
    "gemma-2-2b-it-Q4_K_M.gguf" = "$base\subagents\schema"
    "granite-3.1-2b-instruct-Q4_K_M.gguf" = "$base\subagents\sql"
    "SmolLM2-360M-Instruct-Q4_K_M.gguf" = "$base\subagents\git"
    "Falcon3-3B-Instruct-Q4_K_M.gguf" = "$base\subagents\planner"
    "Qwen2.5-3B-Instruct-Q4_K_M.gguf" = "$base\subagents\search"
}

foreach ($file in $moves.Keys) {
    $src = Join-Path $base $file
    $dest = $moves[$file]
    if (Test-Path $src) {
        Move-Item -Path $src -Destination $dest -Force
        Write-Host "[+] Moved $file -> $dest" -ForegroundColor Green
    }
}

Write-Host "`n[+] Models folder organized successfully!" -ForegroundColor Cyan
