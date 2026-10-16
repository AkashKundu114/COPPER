import re
import subprocess
from pathlib import Path

REPO_ROOT = Path("d:/C.O.P.P.E.R")
commits = subprocess.check_output(['git', 'log', '--oneline'], cwd=REPO_ROOT, text=True, encoding="utf-8").splitlines()

pat = re.compile(r'(?i)(api[_-]?key|secret[_-]?key|private[_-]?key|password|bearer|ghp_[a-zA-Z0-9]{30,}|sk-[a-zA-Z0-9]{32,})')
suspicious = []

filters = [
    'os.getenv', 'getenv', 'settings.', 'Config', 'SecretStr', 'placeholder',
    'dummy', 'example', 'your_', 'test_', '""', "''", 'None', 'Field(',
    'sk-1234', 'CHANGE_ME', 'test-secret', '<password>', 'YOUR_', 'fake',
    'password: str', 'api_key: str', 'Optional[str]', 'password: Optional',
    'mock', 'synth', 'sample', 'CHANGELOG', 'test_data_firewall', 'test_forge_sandbox'
]

for c in commits:
    cid = c.split()[0]
    diff = subprocess.check_output(['git', 'show', '--format=', cid], cwd=REPO_ROOT, text=True, encoding="utf-8", errors='ignore')
    for line in diff.splitlines():
        if line.startswith('+') and not line.startswith('+++'):
            m = pat.search(line)
            if m:
                sline = line[1:].strip()
                if any(x.lower() in sline.lower() for x in filters):
                    continue
                if len(sline) > 15 and ('=' in sline or ':' in sline or '"' in sline):
                    suspicious.append((cid, c, sline[:120]))

print(f"Total commits scanned: {len(commits)}")
print(f"Suspicious lines found in history: {len(suspicious)}")
for s in suspicious[:30]:
    print(f"[{s[0]}] {s[2]}")

with open(REPO_ROOT / "REMEDIATION/logs/git_history_secret_scan.log", "w", encoding="utf-8") as fp:
    fp.write(f"Total commits scanned: {len(commits)}\n")
    fp.write(f"Suspicious lines found: {len(suspicious)}\n\n")
    for s in suspicious:
        fp.write(f"Commit: {s[1]}\nLine: {s[2]}\n\n")
